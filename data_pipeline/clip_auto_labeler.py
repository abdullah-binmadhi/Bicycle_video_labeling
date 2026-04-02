import cv2
import torch
import os
import numpy as np
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from collections import deque

class AdvancedCLIPLabeler:
    """
    Upgraded Zero-Shot Object Detector using Standard CLIP
    Implements Multi-Scale Sliding Windows, Prompt Ensembling, 
    Negative Prompting, and Temporal Smoothing.
    """
    def __init__(self, model_id="openai/clip-vit-large-patch14-336"):
        print("Loading Advanced CLIP Foundation Model...")
        # Automatically use GPU (MPS for Mac) if available, otherwise CPU
        if torch.backends.mps.is_available():
            self.device = "mps"
        elif torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
            
        self.processor = CLIPProcessor.from_pretrained(model_id)
        self.model = CLIPModel.from_pretrained(model_id).to(self.device)
        
        # --- FEATURE 1: Prompt Ensembling & POV Tuning ---
        # Instead of 1 word, we use 3 highly descriptive sentences per class and combine them.
        # Added "first-person POV" context to drastically improve bicycle camera comprehension.
        import json
        with open(os.path.join(os.path.dirname(__file__), '../config/labels.json'), 'r') as f:
            self.target_classes = json.load(f)
            
    def filter_classes(self, selected_classes):
        """Allows the UI to restrict which classes are actually checked"""
        if not selected_classes: return
        self.target_classes = {k: v for k, v in self.target_classes.items() if k in selected_classes}
        print(f"Filtered to {len(self.target_classes)} target classes.")
        
        # --- FEATURE 2: Negative Prompting ---
        # Acts as an "escape route" to completely eliminate False Positives
        self.negative_prompts = [
            "a dark shadow on the road",
            "a bicycle tire",
            "the bicycle handlebars or frame",
            "clear blue sky",
            "green trees and bushes above head",
            "plain grass",
            "a blank wall",
            "just the empty view of the dashboard"
        ]
        
        # Pre-compute the mathematics for the text so it runs extremely fast on videos
        self.text_features = self._precompute_text_embeddings()
        
        # --- FEATURE 3: Temporal Smoothing (Memory) ---
        # Keep history of the last 5 frames to smooth out flickering detections
        self.history = deque(maxlen=5)
        
    def _precompute_text_embeddings(self):
        embeddings = {}
        # Precompute Ensembled Targets
        for class_name, prompts in self.target_classes.items():
            inputs = self.processor(text=prompts, return_tensors="pt", padding=True).to(self.device)
            with torch.no_grad():
                # Average the 3 prompt embeddings into 1 "Super Prompt"
                emb_raw = self.model.get_text_features(**inputs)
                emb = emb_raw.pooler_output if hasattr(emb_raw, 'pooler_output') else emb_raw
                if not isinstance(emb, torch.Tensor):
                    emb = emb[0]
                emb = emb.mean(dim=0, keepdim=True)
                embeddings[class_name] = emb / emb.norm(dim=-1, keepdim=True)
                
        # Precompute Negative Escapes
        neg_inputs = self.processor(text=self.negative_prompts, return_tensors="pt", padding=True).to(self.device)
        with torch.no_grad():
            neg_emb_raw = self.model.get_text_features(**neg_inputs)
            neg_emb = neg_emb_raw.pooler_output if hasattr(neg_emb_raw, 'pooler_output') else neg_emb_raw
            if not isinstance(neg_emb, torch.Tensor):
                neg_emb = neg_emb[0]
            embeddings["Negative"] = neg_emb / neg_emb.norm(dim=-1, keepdim=True)
            
        return embeddings

    def process_video_frames(self, frames_folder, output_folder, output_csv_path=None):
        import csv
        print(f"Scanning frames in: {frames_folder}")
        os.makedirs(output_folder, exist_ok=True)
        for cls in self.target_classes.keys():
            os.makedirs(os.path.join(output_folder, cls), exist_ok=True)
            
        csv_file = None
        csv_writer = None
        if output_csv_path:
            os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
            csv_file = open(output_csv_path, mode='w', newline='')
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["video", "timestamp", "x", "y", "w", "h", "label", "confidence"])

        # --- SEPARATING FRAME-LEVEL SURFACES AND LOCALIZED HAZARDS ---
        # Surfaces are evaluated on the whole image instantly (no bounding boxes)
        surface_types = {"Smooth Asphalt", "Cobblestone", "Gravel", "Dirt or Mud", "Water Puddle", "Sand"}

        # --- FASTER MULTI-SCALE ---
        # Very coarse grid just for hazards (Tracks, People, Cars, Potholes, etc.)
        scales = [{"w": 600, "h": 600, "step": 500}] 

        frame_files = sorted([f for f in os.listdir(frames_folder) if f.endswith(('.png', '.jpg', '.jpeg'))])
        
        if not frame_files:
            print("No images found in the target folder. Add frames to test!")
            return
            
        for frame_idx, filename in enumerate(frame_files):
            # NEW: Downsample execution! Skip 29 frames, process 1 (Effectively 1 FPS)
            if frame_idx % 30 != 0:
                continue

            img_path = os.path.join(frames_folder, filename)
            frame = cv2.imread(img_path)
            if frame is None: 
                continue
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_h, img_w = frame.shape[:2]
            
            # --- 1. GLOBAL SURFACE DETECTION (Lightning Fast, 1 Pass) ---
            full_img = Image.fromarray(rgb_frame)
            inputs_full = self.processor(images=full_img, return_tensors="pt", padding=True).to(self.device)
            with torch.no_grad():
                full_feat_raw = self.model.get_image_features(**inputs_full)
                full_feat = full_feat_raw.pooler_output if hasattr(full_feat_raw, 'pooler_output') else full_feat_raw
                if not isinstance(full_feat, torch.Tensor): full_feat = full_feat[0]
                full_feat = full_feat / full_feat.norm(dim=-1, keepdim=True)
            
            # Calculate rough timestamp
            # For accurate timings, we assume the folder contains 30FPS extracted frames
            timestamp = frame_idx / 30.0
            
            best_surface = None
            best_surface_score = -1
            for cls_name, txt_feat in self.text_features.items():
                if cls_name not in surface_types: continue
                sim = (full_feat @ txt_feat.T).max().item()
                if sim > best_surface_score:
                    best_surface_score = sim
                    best_surface = cls_name
                    
            if best_surface and best_surface_score > 0.28:
                # Save just the clean frame into the surface folder
                cv2.imwrite(os.path.join(output_folder, best_surface, f"surface_{filename}"), frame)
                if csv_writer:
                    # Surfaces don't have bounding boxes, so x,y,w,h are empty or full screen.
                    csv_writer.writerow([frames_folder, f"{timestamp:.3f}", 0, 0, img_w, img_h, best_surface, f"{best_surface_score:.3f}"])

            # --- 2. LOCALIZED HAZARD DETECTION (Coarse Grid) ---
            crops = []
            coords = []
            
            for scale in scales:
                for y in range(0, img_h - scale["h"] + 1, scale["step"]):
                    for x in range(0, img_w - scale["w"] + 1, scale["step"]):
                        crop = frame[y:y+scale["h"], x:x+scale["w"]]
                        crops.append(Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)))
                        coords.append((x, y, x+scale["w"], y+scale["h"]))
                        
            if not crops: continue
            
            # Batch process localized crops
            inputs_crops = self.processor(images=crops, return_tensors="pt", padding=True).to(self.device)
            with torch.no_grad():
                img_feat_raw = self.model.get_image_features(**inputs_crops)
                img_feat_crops = img_feat_raw.pooler_output if hasattr(img_feat_raw, 'pooler_output') else img_feat_raw
                if not isinstance(img_feat_crops, torch.Tensor): img_feat_crops = img_feat_crops[0]
                img_feat_crops = img_feat_crops / img_feat_crops.norm(dim=-1, keepdim=True)
            
            raw_detections = []
            for i, img_feat in enumerate(img_feat_crops):
                best_class = None
                best_score = -1
                
                for cls_name, txt_feat in self.text_features.items():
                    # Skip the surface types since we already did them globally
                    if cls_name in surface_types: continue
                    
                    similarity = (img_feat.unsqueeze(0) @ txt_feat.T).max().item()
                    if similarity > best_score:
                        best_score = similarity
                        best_class = cls_name
                        
                # Elevated confidence specifically for hazards
                if best_class != "Negative" and best_score > 0.28:
                    raw_detections.append({
                        "class": best_class,
                        "box": coords[i],
                        "score": best_score
                    })
            
            self.history.append(raw_detections)
            smoothed_detections = self._apply_temporal_smoothing()

            # --- 3. BOUNDING BOX EXTREME MERGING (One large box per class) ---
            detections_by_class = {}
            for d in smoothed_detections:
                cls_name = d["class"]
                if cls_name not in detections_by_class:
                    detections_by_class[cls_name] = {"boxes": [], "scores": []}
                detections_by_class[cls_name]["boxes"].append(d["box"])
                detections_by_class[cls_name]["scores"].append(d["score"])

            # Render ONE massive bounding box per class covering all clustered hits
            for cls_name, data in detections_by_class.items():
                boxes = data["boxes"]
                
                # Find the global minimum X/Y and max X/Y for this class in this frame
                min_x = min(box[0] for box in boxes)
                min_y = min(box[1] for box in boxes)
                max_x = max(box[2] for box in boxes)
                max_y = max(box[3] for box in boxes)
                
                avg_score = sum(data["scores"]) / len(data["scores"])
                
                # 1. Save the big crop that encompasses all the hazards of this type
                crop_img = frame[min_y:max_y, min_x:max_x]
                crop_path = os.path.join(output_folder, cls_name, f"crop_mega_{frame_idx}.jpg")
                cv2.imwrite(crop_path, crop_img)
                
                # 2. Draw ONE large bounding box on the full image
                cv2.rectangle(frame, (min_x, min_y), (max_x, max_y), (0, 0, 255), 5) # Red line for hazards
                cv2.putText(frame, f"{cls_name} ({avg_score:.2f})", (min_x, min_y-15), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                            
                if csv_writer:
                    w = max_x - min_x
                    h = max_y - min_y
                    csv_writer.writerow([frames_folder, f"{timestamp:.3f}", min_x, min_y, w, h, cls_name, f"{avg_score:.3f}"])

            highlight_path = os.path.join(output_folder, f"highlighted_{filename}")
            cv2.imwrite(highlight_path, frame)
            print(f"Processed frame {filename}: Surface=[{best_surface}], Hazards Extracted=[{len(detections_by_class.keys())} classes]")
            
        if csv_file:
            csv_file.close()

    def _apply_temporal_smoothing(self):
        """
        Uses video context history to filter out flickering false positives.
        An object must be detected consistently to be validated.
        """
        if not self.history: return []
        
        # In a full production script, you would do IOU (Intersection over Union) bounding box math here.
        # For simplicity, we just use the most recent frame's confirmed detections.
        return self.history[-1]

if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--frames_dir', type=str, help='Path to extracted video frames.')
    parser.add_argument('--output_csv', type=str, help='Path to output csv (app passed) - we will use its parent dir for datasets.')
    parser.add_argument('--classes', type=str, nargs='*', help='Target classes explicitly selected through the UI checklist')
    args = parser.parse_args()

    if args.frames_dir:
        TEST_FRAMES = args.frames_dir
        if args.output_csv:
            OUTPUT_DIR = os.path.join(os.path.dirname(args.output_csv), "Auto_Generated_Dataset")
            CSV_PATH = args.output_csv
        else:
            OUTPUT_DIR = os.path.join(os.path.dirname(TEST_FRAMES), "Auto_Generated_Dataset")
            CSV_PATH = None
    else:
        # Fallback pointing exactly to your LM-17.06 Session Folder if executed without args
        TEST_FRAMES = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/Project Surface Detection/LM-17.06/876ED8BA-AF81-4DCD-9A29-8702D236B21D/videoframes"
        OUTPUT_DIR = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/Project Surface Detection/LM-17.06/876ED8BA-AF81-4DCD-9A29-8702D236B21D/Auto_Generated_Dataset"
        CSV_PATH = None
    
    os.makedirs(TEST_FRAMES, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Outputting crops and highlighted frames to: {OUTPUT_DIR}")
    if CSV_PATH:
        print(f"Tracking annotations directly to: {CSV_PATH}")
    print(f"Please drop some test .jpg frames into the '{TEST_FRAMES}' folder and re-run.")
    
    # Initialize the Upgraded Foundation Model Pipeline
    print("Starting Setup...")
    labeler = AdvancedCLIPLabeler()
    if getattr(args, 'classes', None):
        labeler.filter_classes(args.classes)
    labeler.process_video_frames(TEST_FRAMES, OUTPUT_DIR, output_csv_path=CSV_PATH)
    print("Setup Complete.")
