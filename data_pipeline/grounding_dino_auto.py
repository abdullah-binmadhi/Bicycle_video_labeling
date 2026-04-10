import os
import sys
import argparse
import csv
import torch
import cv2
import re
from pathlib import Path
from PIL import Image

try:
    from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
except ImportError:
    print("Please run: pip install transformers")
    sys.exit(1)

def parse_args():
    parser = argparse.ArgumentParser(description="Grounding DINO Auto Annotation")
    parser.add_argument('--frames_dir', type=str, help='Path to extracted frame images', required=True)
    parser.add_argument('--output_csv', type=str, help='Path to save output CSV file', required=True)
    parser.add_argument('--classes', nargs='+', help='Target text prompt to detect', default=["pothole", "crack", "bicycle"])
    parser.add_argument('--out', type=str, default='', help='Ignore')
    # Extra parameters we don't strictly need but electron might send
    parser.add_argument('--use_clip', action='store_true')
    parser.add_argument('--max_frames', type=int, default=0)
    parser.add_argument('--no_save_frames', action='store_true')
    parser.add_argument('--conf', type=float, default=0.25)
    parser.add_argument('--text_conf', type=float, default=0.25)
    parser.add_argument('--model', type=str, default='')
    return parser.parse_args()

def main():
    args = parse_args()
    
    device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"[System] Using device: {device}")
    
    model_id = "IDEA-Research/grounding-dino-base"
    print(f"[System] Loading Grounding DINO model: {model_id}...")
    processor = AutoProcessor.from_pretrained(model_id)
    model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id).to(device)
    
    frames_dir = Path(args.frames_dir)
    out_csv_path = Path(args.output_csv)
    
    # Process classes to extract IDs and clean names
    class_mapping = {}
    clean_classes = []
    
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

    for c in args.classes:
        clean_name = c.lower().replace('_', ' ')
        # extract name if formatted
        match = re.match(r'^(\d+)\s*-\s*(.+)$', c)
        if match:
            clean_name = match.group(2).lower().replace('_', ' ')
            
        # Verify if class is in allowed labels
        matched_allowed = None
        for allowed_k, allowed_v in ALLOWED_LABELS.items():
            if allowed_k in clean_name or clean_name in allowed_k:
                matched_allowed = allowed_k
                break
                
        if matched_allowed:
            formatted_name = f"{ALLOWED_LABELS[matched_allowed]} - {matched_allowed}"
            class_mapping[matched_allowed] = formatted_name
            if matched_allowed not in clean_classes:
                clean_classes.append(matched_allowed)
        else:
            print(f"[Warning] Class '{c}' not in ALLOWED_LABELS, skipping.")
            
    if not clean_classes:
        print("[Error] No valid classes found from ALLOWED_LABELS. Exiting.")
        return
        
    # Text prompt for Grounding DINO needs dot separation and only clean names
    text_prompt = " . ".join(clean_classes) + " ."
    print(f"[System] Text prompt: {text_prompt}")
    
    image_paths = sorted([p for p in frames_dir.glob("*.[jp][pn][g]*")])
    if args.max_frames > 0:
        image_paths = image_paths[:args.max_frames]

    out_csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Also create an annotated images directory
    anno_frames_dir = None
    if not args.no_save_frames:
        anno_frames_dir = out_csv_path.parent / "annotated_frames"
        anno_frames_dir.mkdir(parents=True, exist_ok=True)
    
    with open(out_csv_path, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["frame", "class", "confidence", "xmin", "ymin", "xmax", "ymax", "distance_m"])
        
        for idx, img_path in enumerate(image_paths):
            print(f"Processing {idx+1}/{len(image_paths)}: {img_path.name}")
            
            # Read with cv2 for drawing
            cv_img = cv2.imread(str(img_path))
            if cv_img is None:
                print(f"Failed to read image: {img_path}")
                continue
                
            # Convert to PIL for DINO
            image = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
            
            inputs = processor(images=image, text=text_prompt, return_tensors="pt").to(device)
            with torch.no_grad():
                outputs = model(**inputs)
            
            # Use provided text_conf
            results = processor.post_process_grounded_object_detection(
                outputs,
                inputs.input_ids,
                threshold=args.conf,
                text_threshold=args.text_conf,
                target_sizes=[image.size[::-1]]
            )[0]
            
            for score, label_detected, box in zip(results["scores"], results["labels"], results["boxes"]):
                if score.item() < args.conf:
                    continue
                
                # Match detected label to original format
                detected_name = label_detected.lower()
                
                # Find best matching class from our mapping
                mapped_label = None
                for clean_name, orig_format in class_mapping.items():
                    if clean_name in detected_name or detected_name in clean_name:
                        mapped_label = orig_format
                        break
                        
                if not mapped_label:
                    continue
                
                x_min, y_min, x_max, y_max = map(int, box.tolist())
                
                # Draw bounding box if saving frames
                if not args.no_save_frames and anno_frames_dir:
                    cv2.rectangle(cv_img, (int(x_min), int(y_min)), (int(x_max), int(y_max)), (0, 255, 0), 2)
                    label_text = f"{mapped_label} {score.item():.2f}"
                    cv2.putText(cv_img, label_text, (int(x_min), int(y_min)-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Pseudo distance for structure matching
                distance_m = 10.0
                
                writer.writerow([
                    img_path.name,
                    mapped_label,
                    f"{score.item():.2f}",
                    int(x_min),
                    int(y_min),
                    int(x_max),
                    int(y_max),
                    f"{distance_m:.1f}"
                ])
                
            # Save annotated frame
            if not args.no_save_frames and anno_frames_dir:
                out_img_path = anno_frames_dir / img_path.name
                cv2.imwrite(str(out_img_path), cv_img)
                
    print(f"[System] Finished. Output saved to {out_csv_path}")

if __name__ == "__main__":
    main()
