import os
import sys
import json
import time
import argparse
import re
import numpy as np
import ssl
from PIL import Image

# Bypass SSL certificate verification for model downloads on macOS
ssl._create_default_https_context = ssl._create_unverified_context

try:
    from ultralytics import YOLOWorld
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
    return parser.parse_args()

class TwoStageAnnotator:
    def __init__(self, target_classes, use_clip=False):
        self.device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
        
        print("\n[System] Initializing YOLO-World...")
        # Using YOLO-World for open-vocabulary zero-shot detection
        self.yolo = YOLOWorld("yolov8s-world.pt") # Small model for fast local inference
        
        # Inject the custom target vocabulary into YOLO
        self.target_classes = target_classes
        
        # Clean target classes for YOLO's zero-shot NLP engine (e.g. "133 - bicycle_lane" -> "bicycle lane")
        self.yolo_classes = [re.sub(r'^\d+\s*-\s*', '', c).replace('_', ' ') for c in self.target_classes]
        self.yolo.set_classes(self.yolo_classes)
        print(f"[System] YOLO-World active with NLP vocabulary: {self.yolo_classes}")
        
        self.use_clip = use_clip
        if self.use_clip:
            print("[System] Initializing CLIP Foundation Model for Stage-2 Refinement...")
            model_id = "openai/clip-vit-base-patch32"
            self.clip_processor = CLIPProcessor.from_pretrained(model_id)
            self.clip_model = CLIPModel.from_pretrained(model_id).to(self.device)
            # Create highly descriptive prompt branches for the CLIP evaluator
            self.clip_prompts = [
                f"a close up photo of {c}" for c in self.yolo_classes
            ]
            print(f"[System] CLIP Prompts loaded: {self.clip_prompts}")

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
                # Stage 1: YOLO-World
                results = self.yolo.predict(img_path, conf=0.05, verbose=False)
                objects_in_frame = 0
                
                # Clean the frame name to just timestamp.jpg for standardization
                clean_match = re.search(r'(\d{10,13}(?:\.\d+)?)', img_name)
                clean_name = f"{clean_match.group(1)}.jpg" if clean_match else img_name
                
                # Setup drawing for annotated frame saving
                img_to_draw = None
                if save_frames and annotated_dir:
                    import cv2
                    img_to_draw = cv2.imread(img_path)
                
                with open(csv_path, 'a') as f:
                    for r in results:
                        boxes = r.boxes
                        for box in boxes:
                            cls_id = int(box.cls[0].item())
                            conf = float(box.conf[0].item())
                            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                            label = self.target_classes[cls_id]
                            
                            clip_desc = ""
                            clip_conf = 0.0
                            
                            # Stage 2: CLIP Refinement
                            if self.use_clip:
                                # OpenCV reads as BGR, PIL reads as RGB. YOLO uses OpenCV generally. Let's lazily crop using PIL
                                img_pil = Image.open(img_path).convert('RGB')
                                crop = img_pil.crop((x1, y1, x2, y2))
                                
                                # Safety catch if crop is basically 0px
                                if crop.width > 5 and crop.height > 5:
                                    inputs = self.clip_processor(text=self.clip_prompts, images=crop, return_tensors="pt", padding=True)
                                    inputs = {k: v.to(self.device) for k, v in inputs.items()}
                                    with torch.no_grad():
                                        outputs = self.clip_model(**inputs)
                                        probs = outputs.logits_per_image.softmax(dim=1)[0]
                                        best_idx = probs.argmax().item()
                                        
                                        clip_desc = self.clip_prompts[best_idx].replace(',', '')
                                        clip_conf = probs[best_idx].item()
                            
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
    annotator = TwoStageAnnotator(target_classes=args.classes, use_clip=args.use_clip)
    
    # args.no_save_frames is True when the user toggles OFF saving. 
    # So if it's False, save_frames = True
    should_save_frames = not args.no_save_frames
    annotator.run(args.frames_dir, args.output_csv, max_frames=args.max_frames, save_frames=should_save_frames)

