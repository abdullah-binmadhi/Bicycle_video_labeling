import os
import sys
import json
import time
import argparse
import re
import numpy as np
import ssl
from PIL import Image

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

# Bypass SSL certificate verification for model downloads on macOS
ssl._create_default_https_context = ssl._create_unverified_context

try:
    from ultralytics import YOLO
except ImportError:
    print("Please run: pip install ultralytics")
    sys.exit(1)

import torch
from transformers import CLIPProcessor, CLIPModel

def parse_args():
    parser = argparse.ArgumentParser(description="Multi-Stage Auto Annotation")
    parser.add_argument('--frames_dir', type=str, help='Path to extracted frame images', required=True)
    parser.add_argument('--output_csv', type=str, help='Path to save output CSV file', required=True)
    parser.add_argument('--classes', nargs='+', help='Target YOLO classes to detect', default=["bicycle", "car", "pedestrian", "pothole"])
    parser.add_argument('--out', type=str, default='', help='Ignore')
    parser.add_argument('--use_clip', action='store_true', help='Pass YOLO crops to CLIP for zero-shot description')
    parser.add_argument('--max_frames', type=int, default=0, help='Max frames to process (0 for unlimited)')
    parser.add_argument('--no_save_frames', action='store_true', help='Skip saving annotated image frames')
    parser.add_argument('--conf', type=float, default=0.25, help='YOLO confidence threshold')
    parser.add_argument('--model', type=str, default='yolov8x.pt', help='YOLO model weights')
    return parser.parse_args()

class TwoStageAnnotator:
    def __init__(self, target_classes, use_clip=False, model="yolov8x.pt", conf=0.25):
        self.conf = conf
        self.device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
        
        print(f"\n[System] Initializing Standard YOLO ({model})...")
        self.yolo = YOLO(model)
        
        self.target_classes = target_classes
        
        ALLOWED_LABELS = {
            "bicycle": "1",
            "person": "2",
            "car": "3",
            "motorcycle": "4",
            "bus": "5",
            "truck": "6",
            "traffic light": "7",
            "stop sign": "8"
        }
        
        coco_mapping = {
            "person": 0, "pedestrian": 0,
            "bicycle": 1, "bike": 1,
            "car": 2, "automobile": 2,
            "motorcycle": 3, "motorbike": 3,
            "bus": 5, "truck": 7, "lorry": 7,
            "traffic light": 9, "stop sign": 11
        }
        self.coco_mapping = coco_mapping
        self.allowed_labels = ALLOWED_LABELS
        
        self.yolo_classes = []
        self.yolo_ids = []
        self.yolo_original_labels = []
        self.surface_classes = []
        self.surface_original_labels = []
        
        for c in self.target_classes:
            clean_c = re.sub(r'^\d+\s*-\s*', '', c).lower().replace('_', ' ')
            is_surface = False
            
            # Dictionary mapping for common ambiguous or difficult zero-shot classes
            if "bicycle lane" in clean_c or "bike lane" in clean_c or "bicycle mark" in clean_c or "133" in clean_c:
                clean_c = "bicycle lane marking on the road"
            elif "asphalt" in clean_c:
                clean_c = "patch of dark asphalt road surface"
                is_surface = True
            elif "concrete" in clean_c:
                clean_c = "patch of concrete road surface"
                is_surface = True
            elif "paving" in clean_c or "block" in clean_c or "cobblestone" in clean_c:
                clean_c = "paving block cobblestone brick road surface"
                is_surface = True
            elif "dirt" in clean_c or "unpaved" in clean_c or "gravel" in clean_c:
                clean_c = "unpaved dirt or gravel road surface"
                is_surface = True
            elif "stop sign" in clean_c:
                clean_c = "red octagonal stop sign"
            elif "pothole" in clean_c:
                clean_c = "pothole damage on road surface"
            elif "traffic light" in clean_c:
                clean_c = "traffic light set against the sky"
            elif "crosswalk" in clean_c or "zebra" in clean_c:
                clean_c = "painted pedestrian crosswalk zebra crossing on road"
            elif "sidewalk" in clean_c or "pavement" in clean_c:
                clean_c = "pedestrian sidewalk next to the road"
            elif "speed bump" in clean_c:
                clean_c = "speed bump on the road surface"
            elif "manhole" in clean_c:
                clean_c = "circular metal manhole cover on the road"
            elif "pedestrian" in clean_c or "person" in clean_c:
                clean_c = "pedestrian walking on or near the street"
            elif "car" == clean_c or "automobile" in clean_c:
                clean_c = "car driving or parked on the street"
            elif "bus" in clean_c:
                clean_c = "large passenger bus on the street"
            elif "truck" in clean_c or "lorry" in clean_c:
                clean_c = "delivery truck or lorry on the street"
            elif "van" in clean_c:
                clean_c = "passenger or delivery van on the street"
            elif "motorcycle" in clean_c or "motorbike" in clean_c:
                clean_c = "motorcycle or motorbike on the street"
            elif "bicycle" in clean_c and "lane" not in clean_c and "mark" not in clean_c:
                clean_c = "person riding a bicycle or a parked bicycle"
            elif "yield" in clean_c and "sign" in clean_c:
                clean_c = "triangular yield sign"
            elif "speed limit" in clean_c:
                clean_c = "speed limit traffic sign"
            else:
                # Contextual fallback for anything else
                clean_c = f"{clean_c} on the street or road"
                
            matched_id = None
            for k, v in self.coco_mapping.items():
                if k in clean_c:
                    matched_id = v
                    break
            
            if matched_id is not None and not is_surface:
                self.yolo_classes.append(clean_c)
                self.yolo_ids.append(matched_id)
                self.yolo_original_labels.append(c)
            else:
                self.surface_classes.append(clean_c)
                self.surface_original_labels.append(c)
                
        print(f"[System] YOLO COCO Object classes active: {list(zip(self.yolo_classes, self.yolo_ids))}")
        print(f"[System] CLIP Full-Frame Surface vocabulary: {self.surface_classes}")
        
        self.use_clip = use_clip
        
        # Force CLIP initialization if surfaces are requested, even if YOLO refinement is off
        self.requires_clip = self.use_clip or len(self.surface_classes) > 0
        if self.requires_clip:
            print("[System] Initializing CLIP Foundation Model...")
            model_id = "openai/clip-vit-large-patch14"
            self.clip_processor = CLIPProcessor.from_pretrained(model_id, use_fast=False)
            self.clip_model = CLIPModel.from_pretrained(model_id).to(self.device)
            # Create highly descriptive prompt branches for the CLIP evaluator
            self.clip_prompts = []
            for c in self.yolo_classes:
                self.clip_prompts.append(f"a zoomed in cropped photo of a {c}")
            
            self.surface_prompts = []
            for c in self.surface_classes:
                self.surface_prompts.append(f"a photo looking down at a {c}")
                
            print(f"[System] CLIP Object Prompts loaded: {self.clip_prompts}")
            print(f"[System] CLIP Surface Prompts loaded: {self.surface_prompts}")

    def run(self, input_dir, csv_path, max_frames=0, save_frames=True):
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        
        annotated_dir = None
        if save_frames:
            # Create a parallel 'Annotated_Images' directory beside the Output CSV directory
            csv_dir = os.path.dirname(csv_path)
            # Usually Label/Label.0.csv -> we want Annotated_Images/
            annotated_dir = os.path.join(os.path.dirname(csv_dir), 'Annotated_Images')
            os.makedirs(annotated_dir, exist_ok=True)
            print(f"[System] Saving annotated frames to: {annotated_dir}")
        
        # Grab images
        if not os.path.exists(input_dir):
            print(f"Error: Input directory {input_dir} not found.")
            return

        valid_ext = ('.jpg', '.png', '.jpeg')
        images = [f for f in os.listdir(input_dir) if f.lower().endswith(valid_ext)]
        images.sort()
        
        if max_frames > 0 and len(images) > max_frames:
            step = max(1, len(images) // max_frames)
            images = images[::step][:max_frames]

        total = len(images)
        if total == 0:
            print("No images found to process.")
            return
            
        print(f"\\n[System] Starting automated annotation on {total} frames...")
        
        total_objects = 0
        start_time = time.time()
        
        # Write CSV Header
        with open(csv_path, 'w') as f:
            if self.use_clip:
                f.write("frame,label,confidence,x1,y1,x2,y2,clip_refined_desc,clip_confidence\\n")
            else:
                f.write("frame,label,confidence,x1,y1,x2,y2\\n")
                
        for idx, img_name in enumerate(images):
            img_path = os.path.join(input_dir, img_name)
            
            try:
                objects_in_frame = 0
                
                # Clean the frame name to just timestamp.jpg for standardization
                clean_match = re.search(r'(\d{10,13}(?:\.\d+)?)', img_name)
                clean_name = f"{clean_match.group(1)}.jpg" if clean_match else img_name
                
                # Setup drawing for annotated frame saving
                img_to_draw = None
                img_h, img_w = 1080, 1920
                if save_frames and annotated_dir:
                    import cv2
                    img_to_draw = cv2.imread(img_path)
                    if img_to_draw is not None:
                        img_h, img_w = img_to_draw.shape[:2]
                        
                with open(csv_path, 'a') as f:
                    # Stage 1: Surface Detection (Global CLIP)
                    if self.surface_classes:
                        img_pil = Image.open(img_path).convert('RGB')
                        # Crop the bottom 1/3rd for road surface analysis
                        surface_crop = img_pil.crop((0, img_pil.height * 2 // 3, img_pil.width, img_pil.height))
                        
                        inputs = self.clip_processor(text=self.surface_prompts, images=surface_crop, return_tensors="pt", padding=True)
                        inputs = {k: v.to(self.device) for k, v in inputs.items()}
                        with torch.no_grad():
                            outputs = self.clip_model(**inputs)
                            probs = outputs.logits_per_image.softmax(dim=1)[0]
                            best_idx = probs.argmax().item()
                            surf_conf = probs[best_idx].item()
                            
                            surf_label = self.surface_original_labels[best_idx]
                            surf_desc = self.surface_classes[best_idx].replace(',', '')
                            
                            # Log surface as a global frame tag (coords set to 0)
                            if self.use_clip:
                                f.write(f"{clean_name},{surf_label},{surf_conf:.3f},0,0,0,0,{surf_desc},{surf_conf:.3f}\n")
                            else:
                                f.write(f"{clean_name},{surf_label},{surf_conf:.3f},0,0,0,0\n")
                            
                            objects_in_frame += 1
                            total_objects += 1
                            
                            if img_to_draw is not None:
                                cv2.putText(img_to_draw, f"Surface: {surf_label} ({surf_conf:.2f})", (10, img_h - 20), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 100, 100), 2)
                            
                    # Stage 2: Object Detection (YOLO + CLIP Refinement)
                    if self.yolo_classes:
                        # Lower base conf to cast a wider net when CLIP is active, and lower iou to allow overlapping boxes
                        run_conf = max(0.05, self.conf - 0.15) if self.use_clip else self.conf
                        results = self.yolo.predict(img_path, conf=run_conf, iou=0.45, verbose=False)
                        
                        for r in results:
                            boxes = r.boxes
                            for box in boxes:
                                cls_id = int(box.cls[0].item())
                                
                                # Only process object if it's in our requested target IDs
                                if cls_id not in self.yolo_ids:
                                    continue
                                    
                                idx_in_labels = self.yolo_ids.index(cls_id)
                                orig_label = self.yolo_original_labels[idx_in_labels]
                                
                                # Convert to standard ALLOWED_LABELS format
                                base_class = re.sub(r'^\d+\s*-\s*', '', orig_label).lower().replace('_', ' ')
                                matched_k = None
                                for ak, av in self.allowed_labels.items():
                                    if ak in base_class or base_class in ak:
                                        matched_k = ak
                                        break
                                if matched_k:
                                    label = f"{self.allowed_labels[matched_k]} - {matched_k}"
                                else:
                                    continue # Skip if not in allowed labels
                                
                                conf = float(box.conf[0].item())
                                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                                    
                                clip_desc = ""
                                clip_conf = 0.0
                                crop = None
                                
                                # Stage 3: YOLO Object Refinement
                                if self.use_clip:
                                    # OpenCV reads as BGR, PIL reads as RGB. YOLO uses OpenCV generally. Let's lazily crop using PIL
                                    img_pil = Image.open(img_path).convert('RGB')
                                    crop = img_pil.crop((x1, y1, x2, y2))
                                
                                # Safety catch if crop is basically 0px
                                if crop is not None and crop.width > 5 and crop.height > 5:
                                    inputs = self.clip_processor(text=self.clip_prompts, images=crop, return_tensors="pt", padding=True)
                                    inputs = {k: v.to(self.device) for k, v in inputs.items()}
                                    with torch.no_grad():
                                        outputs = self.clip_model(**inputs)
                                        probs = outputs.logits_per_image.softmax(dim=1)[0]
                                        best_idx = probs.argmax().item()
                                        best_conf = probs[best_idx].item()
                                        
                                        if best_idx != idx_in_labels and best_conf > 0.40:
                                            clip_desc = self.clip_prompts[best_idx].replace(',', '')
                                            clip_conf = best_conf
                                        else:
                                            clip_desc = self.clip_prompts[idx_in_labels].replace(',', '')
                                            clip_conf = probs[idx_in_labels].item()
                                
                                if img_to_draw is not None:
                                    import cv2
                                    cv2.rectangle(img_to_draw, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                    text_label = f"{label} {conf:.2f}"
                                    if self.use_clip and clip_desc:
                                        text_label = f"{clip_desc} {clip_conf:.2f}"
                                    cv2.putText(img_to_draw, text_label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                                    
                                # Save
                                if self.use_clip:
                                    f.write(f"{clean_name},{label},{conf:.3f},{x1},{y1},{x2},{y2},{clip_desc},{clip_conf:.3f}\\n")
                                else:
                                    f.write(f"{clean_name},{label},{conf:.3f},{x1},{y1},{x2},{y2}\\n")
                                
                                objects_in_frame += 1
                                total_objects += 1
                    
                if img_to_draw is not None and objects_in_frame > 0:
                    import cv2
                    cv2.imwrite(os.path.join(annotated_dir, clean_name), img_to_draw)
                
            except Exception as e:
                print(f"Error processing {img_name}: {e}")
                
            # Telemetry for Electron UI
            if idx % 1 == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / (idx + 1)
                rem = avg_time * (total - (idx + 1))
                mins, secs = divmod(int(rem), 60)
                eta_str = f"{mins:02d}:{secs:02d}"
                
                stats = {
                    "frame": f"{idx + 1}/{total}",
                    "objects": total_objects,
                    "eta": eta_str
                }
                print(f"ANNO_STATS: {json.dumps(stats)}", flush=True)

        print("\\n[System] Auto-Annotation Complete!")
        print(f"Labels saved to: {csv_path}")

if __name__ == "__main__":
    args = parse_args()
    print(f"Reading frames from: {args.frames_dir}")
    annotator = TwoStageAnnotator(target_classes=args.classes, use_clip=args.use_clip, model=args.model, conf=args.conf)
    
    # args.no_save_frames is True when the user toggles OFF saving. 
    # So if it's False, save_frames = True
    should_save_frames = not args.no_save_frames
    annotator.run(args.frames_dir, args.output_csv, max_frames=args.max_frames, save_frames=should_save_frames)

