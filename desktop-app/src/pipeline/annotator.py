import os
import torch
import cv2
import json
import logging
from typing import List, Dict, Optional

from pipeline.schema import SchemaValidator, ALLOWED_LABELS

# Assume Grounding DINO is available in path or via pip install
# Since we are mocking the exact framework integration based on standard patterns:
try:
    from groundingdino.util.inference import load_model, load_image, predict
    import groundingdino.datasets.transforms as T
except ImportError:
    logging.warning("Grounding DINO not installed. Using mock inference for demonstration.")
    class MockModel:
        def to(self, device): return self
    class MockImage:
        def __init__(self):
            self.shape = (100, 100, 3)
            
    def load_model(*args, **kwargs): return MockModel()
    def load_image(image_path): return MockImage(), None
    def predict(model, image, caption, box_threshold, text_threshold):
        return torch.tensor([[0.1, 0.1, 0.5, 0.5]]), torch.tensor([0.9]), ["car"]

class GroundingDinoAnnotator:
    def __init__(self, config_path: str, weights_path: str, device: str = "cuda"):
        self.device = device
        logging.info(f"Loading Grounding DINO model on {device}...")
        self.model = load_model(config_path, weights_path)
        if hasattr(self.model, 'to'):
            self.model = self.model.to(device)
            
    def _create_caption(self) -> str:
        """Creates the text prompt based on the allowed labels schema."""
        return " . ".join(ALLOWED_LABELS.keys()) + " ."

    def infer_image(self, image_path: str, box_threshold: float = 0.35, text_threshold: float = 0.25) -> List[Dict]:
        """
        Runs inference and maps raw outputs to pipeline prediction format.
        """
        if not os.path.exists(image_path):
            logging.error(f"Image not found: {image_path}")
            return []

        image_source, image = load_image(image_path)
        caption = self._create_caption()
        
        logging.info(f"Running inference on {image_path} with caption '{caption}'")
        
        boxes, logits, phrases = predict(
            model=self.model,
            image=image,
            caption=caption,
            box_threshold=box_threshold,
            text_threshold=text_threshold
        )
        
        # Grounding DINO outputs normalized [cx, cy, w, h] boxes
        h, w, _ = image_source.shape
        predictions = []
        for box, logit, phrase in zip(boxes, logits, phrases):
            # Convert [cx, cy, w, h] to [xmin, ymin, xmax, ymax]
            cx, cy, bw, bh = box.tolist()
            xmin = max(0.0, cx - bw / 2)
            ymin = max(0.0, cy - bh / 2)
            xmax = min(1.0, cx + bw / 2)
            ymax = min(1.0, cy + bh / 2)
            
            # De-normalize coordinates
            xmin_abs = xmin * w
            ymin_abs = ymin * h
            xmax_abs = xmax * w
            ymax_abs = ymax * h
            
            predictions.append({
                "label": phrase.replace('.', '').strip(),
                "score": float(logit),
                "box": [xmin_abs, ymin_abs, xmax_abs, ymax_abs]
            })
            
        return predictions

    def process_dataset(self, image_dir: str, output_csv: str):
        """Processes an entire directory of images and saves annotations."""
        if not os.path.isdir(image_dir):
            logging.error(f"Image directory not found: {image_dir}")
            return
            
        logging.info(f"Starting auto-annotation for dataset in {image_dir}")
        for filename in os.listdir(image_dir):
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            image_path = os.path.join(image_dir, filename)
            raw_predictions = self.infer_image(image_path)
            
            # Strictly validate and enforce schema before saving
            processed_data = SchemaValidator.process_predictions(raw_predictions)
            
            SchemaValidator.write_to_csv(processed_data, output_csv, filename)
            
        logging.info("Dataset auto-annotation complete.")