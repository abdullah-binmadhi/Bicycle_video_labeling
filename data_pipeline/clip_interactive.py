import argparse
import sys
import json
import cv2
import torch
from PIL import Image
try:
    from transformers import CLIPProcessor, CLIPModel
except ImportError:
    pass
import warnings

# Suppress warnings for cleaner JSON output
warnings.filterwarnings("ignore")

def extract_frame(video_path, timestamp_sec):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0: fps = 30
    frame_idx = int(fps * float(timestamp_sec))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()
    if ret:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), frame.shape
    return None, None

def run_interactive_clip(video_path, timestamp_sec, prompt):
    frame_rgb, shape = extract_frame(video_path, timestamp_sec)
    if frame_rgb is None:
        print(json.dumps({"error": "Could not extract frame"}))
        sys.exit(1)
        
    H, W, _ = shape

    try:
        model_id = "openai/clip-vit-base-patch32" # Use a lighter model for interactive speed
        if torch.backends.mps.is_available():
            device = "mps"
        elif torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"
            
        processor = CLIPProcessor.from_pretrained(model_id)
        model = CLIPModel.from_pretrained(model_id).to(device)
        
        pil_img = Image.fromarray(frame_rgb)
        
        boxes = []
        images = []
        
        # Add full image
        boxes.append([0, 0, W, H])
        images.append(pil_img)
        
        # Add grid 3x3
        step_w = W // 3
        step_h = H // 3
        
        for i in range(3):
            for j in range(3):
                x1 = i * step_w
                y1 = j * step_h
                x2 = min((i+1) * step_w, W)
                y2 = min((j+1) * step_h, H)
                
                boxes.append([x1, y1, x2-x1, y2-y1])
                images.append(pil_img.crop((x1, y1, x2, y2)))
                
        # 2x2 grid (larger overlaps)
        step_w2 = W // 2
        step_h2 = H // 2
        for i in range(2):
            for j in range(2):
                x1 = i * step_w2
                y1 = j * step_h2
                x2 = min((i+1) * step_w2, W)
                y2 = min((j+1) * step_h2, H)
                
                boxes.append([x1, y1, x2-x1, y2-y1])
                images.append(pil_img.crop((x1, y1, x2, y2)))

        inputs = processor(text=[prompt], images=images, return_tensors="pt", padding=True).to(device)
        outputs = model(**inputs)
        logits_per_image = outputs.logits_per_image
        scores = logits_per_image.squeeze().detach().cpu().numpy()
        
        best_idx = 1 + scores[1:].argmax()
        best_score = float(scores[best_idx])
        best_box = boxes[best_idx]
        
        print(json.dumps({
            "success": True,
            "original_width": W,
            "original_height": H,
            "box": best_box,
            "score": best_score,
            "prompt": prompt
        }))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--time", required=True, type=float)
    parser.add_argument("--prompt", required=True)
    args = parser.parse_args()
    
    run_interactive_clip(args.video, args.time, args.prompt)