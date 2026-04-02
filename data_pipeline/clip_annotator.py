import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

import torch
import pandas as pd
import logging
from pathlib import Path
from PIL import Image
from tqdm import tqdm

import warnings
warnings.filterwarnings("ignore")

try:
    import transformers
    transformers.logging.set_verbosity_error()
    from transformers import CLIPProcessor, CLIPModel
except ImportError:
    logging.warning("transformers library not found. Please run: pip install transformers pandas torch pillow")
    CLIPProcessor = None
    CLIPModel = None

import sys
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s', stream=sys.stdout)

# Suppress noisy HTTP request INFO logs from HuggingFace
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("filelock").setLevel(logging.ERROR)

class ZeroShotAnnotator:
    """
    Uses OpenAI's CLIP model to classify extracted bicycle point-of-view 
    video frames into road surface categories without requiring manual labeling.
    """
    def __init__(self, model_id: str = "openai/clip-vit-base-patch32"):
        if CLIPModel is None:
            raise ImportError("Please install `transformers` to use the ZeroShotAnnotator.")
            
        self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        logging.info(f"Loading CLIP model '{model_id}' on {self.device}...")
        
        self.model = CLIPModel.from_pretrained(model_id).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_id)

        # Map exactly to num_classes=3 in config.yaml, 
        # using highly descriptive text for CLIP to understand the image context.
        self.class_prompts = [
            "A point of view photo from a bicycle riding on smooth black asphalt or concrete street.",
            "A point of view photo from a bicycle riding on rough cobblestone or bumpy brick road.",
            "A point of view photo from a bicycle riding on a loose dirt, sand, or gravel path."
        ]
        
        # The shorthand label strings mapped to our prompts
        self.class_labels = ["asphalt", "cobblestone", "dirt_gravel"]

    def annotate_session(self, frames_dir: Path, output_csv: Path) -> pd.DataFrame:
        """
        Runs CLIP inference on all images in a directory. We expect filenames to 
        contain the UNIX timestamp (e.g., 'frame_1688123456789.jpg').
        """
        if not frames_dir.exists():
            logging.error(f"Frames directory {frames_dir} not found.")
            return None

        # Gather all images
        image_files = [f for f in frames_dir.iterdir() if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
        if not image_files:
            logging.warning(f"No images found in {frames_dir}")
            return None

        results = []
        
        logging.info(f"Annotating {len(image_files)} frames in {frames_dir.name}...")
        for img_path in tqdm(image_files):
            try:
                # Extract timestamp from filename. Assuming format: frame_1688123456789.jpg
                # Adjust regex or split logic based on your actual frame extraction script.
                timestamp_str = img_path.stem.split('_')[-1]
                timestamp = float(timestamp_str)
                
                image = Image.open(img_path).convert("RGB")
                inputs = self.processor(text=self.class_prompts, images=image, return_tensors="pt", padding=True)
                
                # Move to device
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    logits_per_image = outputs.logits_per_image # Image-text similarity score
                    probs = logits_per_image.softmax(dim=1).cpu().numpy()
                
                best_class_idx = probs.argmax()
                best_label = self.class_labels[best_class_idx]
                
                results.append({
                    "NTP": timestamp,
                    "Label_Raw": best_label,
                    "Confidence": probs[0][best_class_idx]
                })

            except Exception as e:
                logging.error(f"Failed to process {img_path}: {e}")

        if not results:
            logging.error("No frames were successfully processed.")
            return None

        df = pd.DataFrame(results)
        
        # Sort chronologically
        df.sort_values("NTP", inplace=True)

        # --- TEMPORAL SMOOTHING ---
        # A single frame misclassification (e.g., a glare looking like gravel) 
        # is smoothed out by surrounding context frames. 
        # Using a rolling mode (majority vote) over a window of 3 frames.
        logging.info("Applying temporal smoothing to filter out visual anomalies...")
        
        # Map string to int to use rolling operations
        label_to_id = {label: idx for idx, label in enumerate(self.class_labels)}
        id_to_label = {idx: label for label, idx in label_to_id.items()}
        
        df['Label_ID'] = df['Label_Raw'].map(label_to_id)
        
        # Rolling majority vote (window size 5 representing 5 seconds if 1 FPS)
        df['Label_ID_Smoothed'] = df['Label_ID'].rolling(window=5, center=True, min_periods=1).apply(lambda x: x.mode()[0])
        
        # Map back to string format required by synchronizer
        df['Label'] = df['Label_ID_Smoothed'].map(id_to_label)

        # Drop interim columns and save
        final_df = df[['NTP', 'Label']]
        
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        final_df.to_csv(output_csv, index=False)
        logging.info(f"Saved zero-shot ground truth to {output_csv}")
        
        return final_df

if __name__ == "__main__":
    # Example usage:
    # This logic assumes you extract video frames into BicycleData/Android/<session>/VideoFrames/
    import sys
    
    annotator = ZeroShotAnnotator()
    
    base_data = Path("../Project Surface Detection/BicycleData")
    if not base_data.exists():
         base_data = Path("/Users/abdullahbinmadhi/Desktop/Bicycle ML/Project Surface Detection/BicycleData")
    
    for platform in ['Android', 'iOS']:
        platform_dir = base_data / platform
        if not platform_dir.exists(): continue
            
        for session_dir in platform_dir.iterdir():
            if not session_dir.is_dir(): continue
            
            # Assuming you have a folder named 'VideoFrames' containing the extracted jpgs
            frames_dir = session_dir / "VideoFrames"
            if frames_dir.exists():
                out_csv = session_dir / "Label" / "Label.0.csv"
                annotator.annotate_session(frames_dir, out_csv)
