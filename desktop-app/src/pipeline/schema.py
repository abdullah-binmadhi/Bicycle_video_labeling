import os
import csv
import json
import logging
from typing import List, Dict, Tuple, Set

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Fixed label set based on filtered elements selected for detection
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

REVERSE_LABELS = {v: k for k, v in ALLOWED_LABELS.items()}

class SchemaValidator:
    """Validates and enforces the strict CSV schema for data annotation."""

    @staticmethod
    def validate_label(label: str) -> str:
        """
        Validates and normalizes a label. Returns the label name if valid,
        otherwise raises ValueError. Eliminates unknown/unclassified.
        """
        label_lower = label.strip().lower()
        if label_lower in ALLOWED_LABELS:
            return label_lower
        elif label_lower in REVERSE_LABELS:
            return REVERSE_LABELS[label_lower]
        else:
            raise ValueError(f"Invalid label: '{label}'. Must be one of {list(ALLOWED_LABELS.keys())}.")

    @staticmethod
    def get_label_code(label: str) -> str:
        valid_label = SchemaValidator.validate_label(label)
        return ALLOWED_LABELS[valid_label]

    @staticmethod
    def validate_bbox(bbox: List[float]) -> bool:
        """Validates bounding box format [xmin, ymin, xmax, ymax] normalized 0-1 or absolute."""
        if len(bbox) != 4:
            return False
        if any(not isinstance(v, (int, float)) for v in bbox):
            return False
        if bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
            return False
        return True

    @staticmethod
    def process_predictions(predictions: List[Dict]) -> List[Dict]:
        """
        Processes model predictions, enforcing the schema, filtering invalid labels,
        and mapping label names to codes consistently.
        """
        processed = []
        for pred in predictions:
            try:
                # Assuming pred structure: {"label": "car", "box": [x1,y1,x2,y2], "score": 0.9}
                valid_label = SchemaValidator.validate_label(pred.get("label", ""))
                label_code = SchemaValidator.get_label_code(valid_label)
                box = pred.get("box", [])
                
                if not SchemaValidator.validate_bbox(box):
                    logging.warning(f"Invalid bbox skipped: {box}")
                    continue
                    
                processed.append({
                    "label_code": label_code,
                    "class_name": valid_label,
                    "xmin": box[0],
                    "ymin": box[1],
                    "xmax": box[2],
                    "ymax": box[3],
                    "score": pred.get("score", 0.0)
                })
            except ValueError as e:
                logging.warning(f"Schema Validation Error: {e} - Prediction discarded.")
        
        return processed

    @staticmethod
    def write_to_csv(processed_data: List[Dict], output_file: str, image_id: str):
        """Writes strictly validated data to the CSV schema."""
        file_exists = os.path.isfile(output_file)
        fieldnames = ["image_id", "label_code", "class_name", "xmin", "ymin", "xmax", "ymax", "score"]
        
        try:
            with open(output_file, 'a', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                    
                for item in processed_data:
                    row = {"image_id": image_id}
                    row.update(item)
                    writer.writerow(row)
            logging.info(f"Successfully wrote {len(processed_data)} annotations to {output_file}")
        except Exception as e:
            logging.error(f"Failed to write to CSV: {e}")
