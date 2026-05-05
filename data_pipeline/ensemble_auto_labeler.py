import os
import sys
import json
import time
import argparse
import re
import csv
import numpy as np
from pathlib import Path
from PIL import Image
import io

import torch
import cv2

try:
    from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
except ImportError:
    print("Please run: pip install transformers torch torchvision")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Please run: pip install requests")
    sys.exit(1)

def parse_args():
    parser = argparse.ArgumentParser(description="Zero-Shot Bounding Box Annotator")
    parser.add_argument('--frames_dir', type=str, help='Path to extracted frame images', required=True)
    parser.add_argument('--output_csv', type=str, help='Path to save output CSV file', required=True)
    parser.add_argument('--classes', nargs='+', help='Target classes to detect', default=["bicycle", "car", "pedestrian", "pothole"])
    parser.add_argument('--out', type=str, default='', help='Ignore')
    parser.add_argument('--use_clip', action='store_true', help='Use for full-frame tagging')
    parser.add_argument('--max_frames', type=int, default=0, help='Max frames to process')
    parser.add_argument('--no_save_frames', action='store_true', help='Skip saving annotated images')
    parser.add_argument('--conf', type=float, default=0.15, help='Base confidence threshold')
    parser.add_argument('--text_conf', type=float, default=0.50, help='Text confidence (Ignored)')
    parser.add_argument('--model', type=str, default='google/owlv2-large-patch14-ensemble', help='Model weights')
    # Server-based OWLv2 arguments
    parser.add_argument('--use_server', action='store_true', help='Use remote server OWLv2 API')
    parser.add_argument('--server_endpoint', type=str, default='', help='Server API endpoint URL')
    parser.add_argument('--server_api_key', type=str, default='', help='API key for server authentication')
    return parser.parse_args()

class ServerBasedAnnotator:
    """Remote OWLv2 inference via HTTP API"""
    def __init__(self, target_classes, server_endpoint, api_key, conf=0.15):
        self.conf = conf
        self.target_classes = target_classes
        self.server_endpoint = server_endpoint
        self.api_key = api_key
        self.surface_types = {
            "asphalt", "smooth asphalt", "rough asphalt", "gravel", "sand", "mud", 
            "cobblestone", "brick paving", "concrete pavers", "dirt road", 
            "macadam", "grassy path", "wood planks", "metal grating", 
            "paved path", "unpaved path", "ice", "snow"
        }
        print(f"\n[Server] Initialized with API endpoint: {server_endpoint}")

    def infer_frame(self, img_path):
        """Send frame to server API and get detections"""
        try:
            with open(img_path, 'rb') as f:
                files = {'file': f}
                # Format queries as comma-separated text
                queries_text = ", ".join(self.target_classes)
                data = {
                    'queries': queries_text,
                    'threshold': str(self.conf)
                }
                headers = {
                    'Authorization': f'Bearer {self.api_key}'
                }
                
                response = requests.post(
                    self.server_endpoint,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=60
                )
                
                if response.status_code != 200:
                    print(f"[Server] API Error {response.status_code}: {response.text[:200]}")
                    return []
                
                result = response.json()
                return result.get('detections', [])
                
        except Exception as e:
            print(f"[Server] Request failed: {str(e)}")
            return []

    def run(self, input_dir, csv_path, max_frames=0, save_frames=True):
        import shutil
        csv_dir = os.path.dirname(csv_path)
        if csv_dir:
            os.makedirs(csv_dir, exist_ok=True)
        
        annotated_dir = None
        if save_frames:
            annotated_dir = os.path.join(csv_dir, 'Visual_Debugging')
            os.makedirs(annotated_dir, exist_ok=True)
        
        valid_ext = ('.jpg', '.png', '.jpeg')
        images = [f for f in os.listdir(input_dir) if f.lower().endswith(valid_ext)]
        images.sort()
        
        if max_frames > 0 and len(images) > max_frames:
            step = max(1, len(images) // max_frames)
            images = images[::step][:max_frames]

        total = len(images)
        if total == 0: return

        print(f"\n[Server] Starting Remote OWLv2 Pipeline on {total} frames...")
        start_time = time.time()
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'label_code', 'class_name', 'xmin', 'ymin', 'xmax', 'ymax', 'score'])
            
            for idx, img_name in enumerate(images):
                img_path = os.path.join(input_dir, img_name)
                clean_match = re.search(r'(\d{10,13}(?:\.\d+)?)', img_name)
                clean_name = f"{clean_match.group(1)}.jpg" if clean_match else img_name
                
                dest_img_path = os.path.join(csv_dir, clean_name)
                if os.path.abspath(img_path) != os.path.abspath(dest_img_path):
                    shutil.copy2(img_path, dest_img_path)
                
                img_to_draw = cv2.imread(img_path) if save_frames else None
                img_pil = Image.open(img_path).convert('RGB')
                
                # Get detections from server
                detections = self.infer_frame(img_path)
                
                frame_predictions = []
                for det in detections:
                    if isinstance(det, dict) and 'bbox' in det and 'class' in det:
                        # Expected format: {"bbox": [x1, y1, x2, y2], "class": "...", "conf": ...}
                        box = det['bbox']
                        label = det['class']
                        conf_val = float(det.get('conf', 0.5))
                        frame_predictions.append({"label": label, "conf": conf_val, "box": box})
                
                best_surface_preds = {}
                final_predictions = []
                
                for pred in frame_predictions:
                    clean_label = re.sub(r'^\d+\s*-\s*', '', pred["label"]).lower().replace('_', ' ')
                    
                    if clean_label in self.surface_types or clean_label == "bicycle lane":
                        if clean_label not in best_surface_preds or pred["conf"] > best_surface_preds[clean_label]["conf"]:
                            best_surface_preds[clean_label] = pred
                    else:
                        final_predictions.append(pred)
                        
                for bs_pred in best_surface_preds.values():
                    final_predictions.append(bs_pred)
                    
                found_objects = 0
                for pred in final_predictions:
                    label_raw = pred["label"]
                    label_code = "0"
                    if "-" in label_raw:
                        parts = label_raw.split("-", 1)
                        label_code = parts[0].strip()
                        class_name = parts[1].strip()
                    else:
                        class_name = label_raw
                        
                    abs_dest_img_path = os.path.abspath(dest_img_path)
                    x1, y1, x2, y2 = [int(v) for v in pred["box"]]
                    
                    writer.writerow([abs_dest_img_path, label_code, class_name, x1, y1, x2, y2, f"{pred['conf']:.3f}"])
                    found_objects += 1
                    
                    if img_to_draw is not None:
                        cv2.rectangle(img_to_draw, (x1, y1), (x2, y2), (255, 100, 100), 2)
                        text_label = f"{pred['label']} ({pred['conf']:.2f})"
                        cv2.putText(img_to_draw, text_label, (x1, max(y1 - 10, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 100, 100), 2)

                if save_frames and img_to_draw is not None:
                    cv2.imwrite(os.path.join(annotated_dir, clean_name), img_to_draw)
                    
                if idx % 1 == 0:
                    elapsed = time.time() - start_time
                    avg_time = elapsed / (idx + 1)
                    rem = avg_time * (total - (idx + 1))
                    mins, secs = divmod(int(rem), 60)
                    stats = {"frame": f"{idx + 1}/{total}", "objects": found_objects, "eta": f"{mins:02d}:{secs:02d}"}
                    print(f"ANNO_STATS: {json.dumps(stats)}", flush=True)

        print("\n[Server] Remote OWLv2 Auto-Annotation Complete!")
        print(f"Labels saved to: {csv_path}")


class ZeroShotAnnotator:
    """Local OWLv2 inference using transformers library"""
    
    def __init__(self, target_classes, model="google/owlv2-large-patch14-ensemble", conf=0.15):
        self.conf = conf
        self.device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
        
        print(f"\n[System] Initializing Zero-Shot Bounding Box Model ({model})...")
        self.processor = AutoProcessor.from_pretrained(model, use_fast=True)
        self.model = AutoModelForZeroShotObjectDetection.from_pretrained(model).to(self.device)
        
        self.target_classes = target_classes
        self.prompts = []
        
        # Surface types that should only yield one overall classification per frame
        self.surface_types = {
            "asphalt", "smooth asphalt", "rough asphalt", "gravel", "sand", "mud", 
            "cobblestone", "brick paving", "concrete pavers", "dirt road", 
            "macadam", "grassy path", "wood planks", "metal grating", 
            "paved path", "unpaved path", "ice", "snow"
        }
        
        for c in self.target_classes:
            clean_c = re.sub(r'^\d+\s*-\s*', '', c).lower().replace('_', ' ')
            
            # Avoid confusing "bicycle" with "bicycle lane"
            if clean_c == "bicycle lane":
                clean_c = "bicycle lane painted on the road surface"
                
            # OWL-ViT accuracy is much better using raw nouns
            self.prompts.append(clean_c)

    def run(self, input_dir, csv_path, max_frames=0, save_frames=True):
        import shutil
        csv_dir = os.path.dirname(csv_path)
        if csv_dir:
            os.makedirs(csv_dir, exist_ok=True)
        
        annotated_dir = None
        if save_frames:
            annotated_dir = os.path.join(csv_dir, 'Visual_Debugging')
            os.makedirs(annotated_dir, exist_ok=True)
        
        valid_ext = ('.jpg', '.png', '.jpeg')
        images = [f for f in os.listdir(input_dir) if f.lower().endswith(valid_ext)]
        images.sort()
        
        if max_frames > 0 and len(images) > max_frames:
            step = max(1, len(images) // max_frames)
            images = images[::step][:max_frames]

        total = len(images)
        if total == 0: return

        print(f"\n[System] Starting Bounding-Box Pipeline on {total} frames...")
        start_time = time.time()
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'label_code', 'class_name', 'xmin', 'ymin', 'xmax', 'ymax', 'score'])
            
            for idx, img_name in enumerate(images):
                img_path = os.path.join(input_dir, img_name)
                clean_match = re.search(r'(\d{10,13}(?:\.\d+)?)', img_name)
                clean_name = f"{clean_match.group(1)}.jpg" if clean_match else img_name
                
                dest_img_path = os.path.join(csv_dir, clean_name)
                if os.path.abspath(img_path) != os.path.abspath(dest_img_path):
                    shutil.copy2(img_path, dest_img_path)
                
                img_to_draw = cv2.imread(img_path) if save_frames else None
                img_pil = Image.open(img_path).convert('RGB')
                
                # Predict Bounding Boxes via OWL-ViT
                if self.prompts:
                    inputs = self.processor(text=[self.prompts], images=img_pil, return_tensors="pt").to(self.device)
                    with torch.no_grad():
                        outputs = self.model(**inputs)
                        
                    target_sizes = torch.tensor([img_pil.size[::-1]])
                    
                    try:
                        results = self.processor.post_process_grounded_object_detection(outputs=outputs, threshold=self.conf, target_sizes=target_sizes, text_labels=[self.target_classes])[0]
                    except TypeError:
                        # Fallback for older versions or slightly different signatures
                        results = self.processor.post_process_grounded_object_detection(outputs=outputs, threshold=self.conf, target_sizes=target_sizes)[0]
                    
                    found_objects = 0
                    frame_predictions = []
                    
                    for score, label_val, box in zip(results["scores"], results["labels"], results["boxes"]):
                        conf_val = score.item()
                        
                        if isinstance(label_val, str):
                            label = label_val
                        else:
                            label_id = label_val.item()
                            if label_id >= len(self.target_classes): continue
                            label = self.target_classes[label_id]
                            
                        box_list = [int(i) for i in box.tolist()]
                        frame_predictions.append({"label": label, "conf": conf_val, "box": box_list})
                        
                    best_surface_preds = {}
                    final_predictions = []
                    
                    for pred in frame_predictions:
                        clean_label = re.sub(r'^\d+\s*-\s*', '', pred["label"]).lower().replace('_', ' ')
                        
                        # Apply the 1-box-per-frame rule for broad surfaces and bicycle lanes
                        if clean_label in self.surface_types or clean_label == "bicycle lane":
                            if clean_label not in best_surface_preds or pred["conf"] > best_surface_preds[clean_label]["conf"]:
                                best_surface_preds[clean_label] = pred
                        else:
                            # Standard objects (potholes, cars, etc) can have multiple bounding boxes
                            final_predictions.append(pred)
                            
                    for bs_pred in best_surface_preds.values():
                        final_predictions.append(bs_pred)
                        
                    for pred in final_predictions:
                        label_raw = pred["label"]
                        label_code = "0"
                        if "-" in label_raw:
                            parts = label_raw.split("-", 1)
                            label_code = parts[0].strip()
                            class_name = parts[1].strip()
                        else:
                            class_name = label_raw
                            
                        # 'image_id' must be the absolute path of the clean image in the output directory
                        abs_dest_img_path = os.path.abspath(dest_img_path)
                        x1, y1, x2, y2 = pred["box"]
                        
                        writer.writerow([abs_dest_img_path, label_code, class_name, x1, y1, x2, y2, f"{pred['conf']:.3f}"])
                        found_objects += 1
                        
                        if img_to_draw is not None:
                            cv2.rectangle(img_to_draw, (x1, y1), (x2, y2), (255, 100, 100), 2)
                            text_label = f"{pred['label']} ({pred['conf']:.2f})"
                            cv2.putText(img_to_draw, text_label, (x1, max(y1 - 10, 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 100, 100), 2)

                if save_frames and img_to_draw is not None:
                    cv2.imwrite(os.path.join(annotated_dir, clean_name), img_to_draw)
                    
                if idx % 1 == 0:
                    elapsed = time.time() - start_time
                    avg_time = elapsed / (idx + 1)
                    rem = avg_time * (total - (idx + 1))
                    mins, secs = divmod(int(rem), 60)
                    stats = {"frame": f"{idx + 1}/{total}", "objects": found_objects, "eta": f"{mins:02d}:{secs:02d}"}
                    print(f"ANNO_STATS: {json.dumps(stats)}", flush=True)

        print("\n[System] Bounding-Box Auto-Annotation Complete!")
        print(f"Labels saved to: {csv_path}")

if __name__ == "__main__":
    args = parse_args()
    
    # Choose annotator based on mode
    if args.use_server:
        if not args.server_endpoint or not args.server_api_key:
            print("[Error] --server_endpoint and --server_api_key are required when using --use_server")
            sys.exit(1)
        annotator = ServerBasedAnnotator(
            target_classes=args.classes,
            server_endpoint=args.server_endpoint,
            api_key=args.server_api_key,
            conf=args.conf
        )
    else:
        annotator = ZeroShotAnnotator(
            target_classes=args.classes,
            model=args.model,
            conf=args.conf
        )
    
    annotator.run(args.frames_dir, args.output_csv, max_frames=args.max_frames, save_frames=not args.no_save_frames)
