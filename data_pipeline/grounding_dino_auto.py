import os
import sys
import argparse
import csv
import torch
import cv2
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
    
    # Text prompt for Grounding DINO needs dot separation
    text_prompt = ". ".join(args.classes) + "."
    print(f"[System] Text prompt: {text_prompt}")
    
    image_paths = sorted([p for p in frames_dir.glob("*.[jp][pn][g]*")])
    if args.max_frames > 0:
        image_paths = image_paths[:args.max_frames]

    out_csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_csv_path, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["frame", "class", "confidence", "xmin", "ymin", "xmax", "ymax", "distance_m"])
        
        for idx, img_path in enumerate(image_paths):
            print(f"Processing {idx+1}/{len(image_paths)}: {img_path.name}")
            image = Image.open(img_path).convert("RGB")
            
            inputs = processor(images=image, text=text_prompt, return_tensors="pt").to(device)
            with torch.no_grad():
                outputs = model(**inputs)
            
            # Use provided text_conf
            results = processor.post_process_grounded_object_detection(
                outputs,
                inputs.input_ids,
                box_threshold=args.conf,
                text_threshold=args.text_conf,
                target_sizes=[image.size[::-1]]
            )[0]
            
            for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
                if score.item() < args.conf:
                    continue
                
                x_min, y_min, x_max, y_max = box.tolist()
                
                # Pseudo distance for structure matching
                distance_m = 10.0
                
                writer.writerow([
                    img_path.name,
                    label,
                    f"{score.item():.2f}",
                    int(x_min),
                    int(y_min),
                    int(x_max),
                    int(y_max),
                    f"{distance_m:.1f}"
                ])
                
    print(f"[System] Finished. Output saved to {out_csv_path}")

if __name__ == "__main__":
    main()
