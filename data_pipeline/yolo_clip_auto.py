import os
import sys
import json
import time
import argparse
import numpy as np
from PIL import Image

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
    return parser.parse_args()

class TwoStageAnnotator:
    def __init__(self, target_classes, use_clip=False):
        self.device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
        
        print("\n[System] Initializing YOLO-World...")
        # Using YOLO-World for open-vocabulary zero-shot detection
        self.yolo = YOLOWorld("yolov8s-world.pt") # Small model for fast local inference
        
        # Inject the custom target vocabulary into YOLO
        self.target_classes = target_classes
        self.yolo.set_classes(self.target_classes)
        print(f"[System] YOLO-World active with vocabulary: {self.target_classes}")
        
        self.use_clip = use_clip
        if self.use_clip:
            print("[System] Initializing CLIP Foundation Model for Stage-2 Refinement...")
            model_id = "openai/clip-vit-base-patch32"
            self.clip_processor = CLIPProcessor.from_pretrained(model_id)
            self.clip_model = CLIPModel.from_pretrained(model_id).to(self.device)
            # Create highly descriptive prompt branches for the CLIP evaluator
            self.clip_prompts = [
                f"a close up photo of {c}" for c in self.target_classes
            ]
            print(f"[System] CLIP Prompts loaded: {self.clip_prompts}")

    def run(self, input_dir, csv_path):
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        
        # Grab images
        if not os.path.exists(input_dir):
            print(f"Error: Input directory {input_dir} not found.")
            return

        valid_ext = ('.jpg', '.png', '.jpeg')
        images = [f for f in os.listdir(input_dir) if f.lower().endswith(valid_ext)]
        images.sort()
        
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
                results = self.yolo.predict(img_path, conf=0.15, verbose=False)
                objects_in_frame = 0
                
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
                                        
                            # Save
                            if self.use_clip:
                                f.write(f"{img_name},{label},{conf:.3f},{x1},{y1},{x2},{y2},{clip_desc},{clip_conf:.3f}\\n")
                            else:
                                f.write(f"{img_name},{label},{conf:.3f},{x1},{y1},{x2},{y2}\\n")
                            
                            objects_in_frame += 1
                            total_objects += 1
                
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
    annotator.run(args.frames_dir, args.output_csv)

