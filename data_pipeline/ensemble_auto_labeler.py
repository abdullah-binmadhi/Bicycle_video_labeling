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

import torch
import cv2

try:
    from ultralytics import YOLO
    from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection, CLIPProcessor, CLIPModel
except ImportError:
    print("Please run: pip install ultralytics transformers")
    sys.exit(1)

def parse_args():
    parser = argparse.ArgumentParser(description="Ensemble Auto Annotation (YOLO + DINO + CLIP)")
    parser.add_argument('--frames_dir', type=str, help='Path to extracted frame images', required=True)
    parser.add_argument('--output_csv', type=str, help='Path to save output CSV file', required=True)
    parser.add_argument('--classes', nargs='+', help='Target classes to detect', default=["bicycle", "car", "pedestrian", "pothole"])
    parser.add_argument('--out', type=str, default='', help='Ignore')
    parser.add_argument('--use_clip', action='store_true', help='Use CLIP for full-frame surface tagging')
    parser.add_argument('--max_frames', type=int, default=0, help='Max frames to process')
    parser.add_argument('--no_save_frames', action='store_true', help='Skip saving annotated images')
    parser.add_argument('--conf', type=float, default=0.25, help='Base confidence threshold')
    parser.add_argument('--text_conf', type=float, default=0.25, help='Text confidence for DINO')
    parser.add_argument('--model', type=str, default='yolo11x.pt', help='YOLO model weights')
    return parser.parse_args()

def calculate_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    if inter_area == 0:
        return 0.0

    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

    iou = inter_area / float(box1_area + box2_area - inter_area)
    return iou

class EnsembleAnnotator:
    def __init__(self, target_classes, model="yolo11x.pt", conf=0.25, text_conf=0.25):
        self.conf = conf
        self.text_conf = text_conf
        self.device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
        
        print(f"\n[System] Initializing Standard YOLO ({model})...")
        self.yolo = YOLO(model)
        
        print(f"[System] Initializing Grounding DINO...")
        dino_model_id = "IDEA-Research/grounding-dino-base"
        self.dino_processor = AutoProcessor.from_pretrained(dino_model_id)
        self.dino_model = AutoModelForZeroShotObjectDetection.from_pretrained(dino_model_id).to(self.device)
        
        print(f"[System] Initializing CLIP Foundation Model...")
        clip_model_id = "openai/clip-vit-large-patch14"
        self.clip_processor = CLIPProcessor.from_pretrained(clip_model_id, use_fast=False)
        self.clip_model = CLIPModel.from_pretrained(clip_model_id).to(self.device)
        
        self.target_classes = target_classes
        
        self.ALLOWED_LABELS = {
            "bicycle": "1", "person": "2", "car": "3", "motorcycle": "4",
            "bus": "5", "truck": "6", "traffic light": "7", "stop sign": "8",
            "pothole": "1", "crack": "8", "pothole cluster": "108"
        }
        
        coco_mapping = {
            "person": 0, "pedestrian": 0, "bicycle": 1, "bike": 1,
            "car": 2, "automobile": 2, "motorcycle": 3, "motorbike": 3,
            "bus": 5, "truck": 7, "lorry": 7, "traffic light": 9, "stop sign": 11
        }
        
        self.yolo_classes = []
        self.yolo_ids = []
        self.yolo_original_labels = []
        self.dino_classes = []
        self.surface_classes = []
        self.surface_original_labels = []
        
        for c in self.target_classes:
            clean_c = re.sub(r'^\d+\s*-\s*', '', c).lower().replace('_', ' ')
            is_surface = False
            
            if "bicycle lane" in clean_c or "bike lane" in clean_c or "133" in clean_c:
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
            elif "pothole" in clean_c:
                self.dino_classes.append(c)
                continue
            elif "crack" in clean_c:
                self.dino_classes.append(c)
                continue
                
            matched_id = None
            for k, v in coco_mapping.items():
                if k in clean_c:
                    matched_id = v
                    break
            
            if matched_id is not None and not is_surface:
                self.yolo_classes.append(clean_c)
                self.yolo_ids.append(matched_id)
                self.yolo_original_labels.append(c)
            elif is_surface:
                self.surface_classes.append(clean_c)
                self.surface_original_labels.append(c)
            else:
                self.dino_classes.append(c)
                
        # DINO prompt preparation
        dino_clean_names = []
        self.dino_class_mapping = {}
        for c in self.dino_classes:
            clean_name = c.lower().replace('_', ' ')
            match = re.match(r'^(\d+)\s*-\s*(.+)$', c)
            if match:
                class_id = match.group(1)
                clean_name = match.group(2).lower().replace('_', ' ')
                formatted_name = f"{class_id} - {clean_name}"
            else:
                formatted_name = c
                
            self.dino_class_mapping[clean_name] = formatted_name
            if clean_name not in dino_clean_names:
                dino_clean_names.append(clean_name)
        
        self.dino_prompt = " . ".join(dino_clean_names) + " ." if dino_clean_names else ""
        
        self.surface_prompts = []
        for c in self.surface_classes:
            self.surface_prompts.append(f"a photo looking down at a {c}")

        self.history_buffer = []  # For temporal smoothing
        self.history_frames = 3   # Require detection in at least 2 out of last 3 frames to emit
        
    def add_to_history(self, current_frame_boxes):
        self.history_buffer.append(current_frame_boxes)
        if len(self.history_buffer) > self.history_frames:
            self.history_buffer.pop(0)

    def temporal_smooth(self, current_frame_boxes):
        if not self.history_buffer:
            return current_frame_boxes
            
        smoothed_boxes = []
        for box in current_frame_boxes:
            box_coords = box['bbox']
            label = box['label']
            
            # Count appearances in history
            appearances = 1 # Appears in current frame
            for hist_frame in self.history_buffer[:-1]: # exclude current
                found = False
                for hist_box in hist_frame:
                    if hist_box['label'] == label and calculate_iou(box_coords, hist_box['bbox']) > 0.5:
                        found = True
                        break
                if found:
                    appearances += 1
                    
            if appearances >= min(2, len(self.history_buffer)):
                smoothed_boxes.append(box)
                
        return smoothed_boxes

    def run(self, input_dir, csv_path, max_frames=0, save_frames=True):
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        
        annotated_dir = None
        if save_frames:
            csv_dir = os.path.dirname(csv_path)
            annotated_dir = os.path.join(os.path.dirname(csv_dir), 'Annotated_Images')
            os.makedirs(annotated_dir, exist_ok=True)
        
        valid_ext = ('.jpg', '.png', '.jpeg')
        images = [f for f in os.listdir(input_dir) if f.lower().endswith(valid_ext)]
        images.sort()
        
        if max_frames > 0 and len(images) > max_frames:
            step = max(1, len(images) // max_frames)
            images = images[::step][:max_frames]

        total = len(images)
        if total == 0: return

        print(f"\\n[System] Starting Ensemble Pipeline on {total} frames...")
        start_time = time.time()
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["frame", "label", "confidence", "x1", "y1", "x2", "y2"])
            
            for idx, img_name in enumerate(images):
                img_path = os.path.join(input_dir, img_name)
                clean_match = re.search(r'(\d{10,13}(?:\.\d+)?)', img_name)
                clean_name = f"{clean_match.group(1)}.jpg" if clean_match else img_name
                
                img_to_draw = cv2.imread(img_path) if save_frames else None
                img_pil = Image.open(img_path).convert('RGB')
                
                current_detections = []
                
                # 1. CLIP Surface Tagging
                if self.surface_prompts:
                    surface_crop = img_pil.crop((0, img_pil.height // 2, img_pil.width, img_pil.height))
                    inputs = self.clip_processor(text=self.surface_prompts, images=surface_crop, return_tensors="pt", padding=True)
                    inputs = {k: v.to(self.device) for k, v in inputs.items()}
                    with torch.no_grad():
                        outputs = self.clip_model(**inputs)
                        probs = outputs.logits_per_image.softmax(dim=1)[0]
                        best_idx = probs.argmax().item()
                        surf_conf = probs[best_idx].item()
                        surf_label = self.surface_original_labels[best_idx]
                        
                        writer.writerow([clean_name, surf_label, f"{surf_conf:.3f}", 0, 0, 0, 0])
                        
                        if img_to_draw is not None:
                            cv2.putText(img_to_draw, f"Surface: {surf_label} ({surf_conf:.2f})", (10, img_to_draw.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 100, 100), 2)

                # 2. YOLO11 Detection
                if self.yolo_classes:
                    results = self.yolo.predict(img_path, conf=self.conf, iou=0.45, verbose=False)
                    for r in results:
                        for box in r.boxes:
                            cls_id = int(box.cls[0].item())
                            if cls_id not in self.yolo_ids: continue
                                
                            idx_in_labels = self.yolo_ids.index(cls_id)
                            orig_label = self.yolo_original_labels[idx_in_labels]
                            
                            label = orig_label
                            conf = float(box.conf[0].item())
                            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                            current_detections.append({'label': label, 'conf': conf, 'bbox': [x1, y1, x2, y2], 'source': 'yolo'})
                
                # 3. Grounding DINO Detection
                if self.dino_prompt:
                    inputs = self.dino_processor(images=img_pil, text=self.dino_prompt, return_tensors="pt").to(self.device)
                    with torch.no_grad():
                        outputs = self.dino_model(**inputs)
                    
                    results = self.dino_processor.post_process_grounded_object_detection(
                        outputs, inputs.input_ids, threshold=self.conf, text_threshold=self.text_conf, target_sizes=[img_pil.size[::-1]]
                    )[0]
                    
                    for score, label_detected, box in zip(results["scores"], results["labels"], results["boxes"]):
                        if score.item() < self.conf: continue
                        
                        detected_name = label_detected.lower()
                        mapped_label = next((orig for clean, orig in self.dino_class_mapping.items() if clean in detected_name or detected_name in clean), None)
                        
                        if mapped_label:
                            x1, y1, x2, y2 = map(int, box.tolist())
                            # IoU Merging with YOLO
                            is_duplicate = False
                            for d in current_detections:
                                if calculate_iou([x1, y1, x2, y2], d['bbox']) > 0.6:
                                    is_duplicate = True
                                    if score.item() > d['conf']:
                                        d['conf'] = score.item()
                                        d['label'] = mapped_label
                                        d['bbox'] = [x1, y1, x2, y2]
                                    break
                            
                            if not is_duplicate:
                                current_detections.append({'label': mapped_label, 'conf': score.item(), 'bbox': [x1, y1, x2, y2], 'source': 'dino'})

                # Temporal Smoothing
                self.add_to_history(current_detections)
                smoothed_detections = self.temporal_smooth(current_detections)

                # Write to CSV and Draw
                for d in smoothed_detections:
                    writer.writerow([clean_name, d['label'], f"{d['conf']:.3f}"] + d['bbox'])
                    if img_to_draw is not None:
                        color = (0, 255, 0) if d['source'] == 'yolo' else (255, 165, 0)
                        cv2.rectangle(img_to_draw, (d['bbox'][0], d['bbox'][1]), (d['bbox'][2], d['bbox'][3]), color, 2)
                        cv2.putText(img_to_draw, f"{d['label']} {d['conf']:.2f}", (d['bbox'][0], d['bbox'][1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                if save_frames and img_to_draw is not None and (smoothed_detections or self.surface_prompts):
                    cv2.imwrite(os.path.join(annotated_dir, clean_name), img_to_draw)
                    
                if idx % 1 == 0:
                    elapsed = time.time() - start_time
                    avg_time = elapsed / (idx + 1)
                    rem = avg_time * (total - (idx + 1))
                    mins, secs = divmod(int(rem), 60)
                    stats = {"frame": f"{idx + 1}/{total}", "objects": len(smoothed_detections), "eta": f"{mins:02d}:{secs:02d}"}
                    print(f"ANNO_STATS: {json.dumps(stats)}", flush=True)

        print("\\n[System] Ensemble Auto-Annotation Complete!")
        print(f"Labels saved to: {csv_path}")

if __name__ == "__main__":
    args = parse_args()
    annotator = EnsembleAnnotator(target_classes=args.classes, model=args.model, conf=args.conf, text_conf=args.text_conf)
    annotator.run(args.frames_dir, args.output_csv, max_frames=args.max_frames, save_frames=not args.no_save_frames)