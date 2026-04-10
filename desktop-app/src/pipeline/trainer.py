import os
import csv
import logging
from typing import Set

from pipeline.schema import SchemaValidator

def validate_csv(csv_path: str):
    """
    Synchronizes dataset preparation by validating the CSV prior to training.
    Validates the schema, ensuring no unclassified labels and strict mapping.
    """
    if not os.path.exists(csv_path):
        logging.error(f"Dataset CSV not found: {csv_path}")
        return False
        
    logging.info(f"Validating dataset CSV at {csv_path}")
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        required_fields = ["image_id", "label_code", "class_name", "xmin", "ymin", "xmax", "ymax", "score"]
        
        fieldnames = reader.fieldnames or []
        if not set(required_fields).issubset(set(fieldnames)):
            logging.error(f"CSV schema mismatch. Required: {required_fields}, Found: {fieldnames}")
            return False
            
        row_num = 1
        valid_rows = 0
        error_rows = 0
        
        for row in reader:
            row_num += 1
            try:
                # Synchronize Class Name and Code Integrity
                label = row["class_name"]
                code = row["label_code"]
                
                # Check for "unknown" or "unclassified"
                if label.lower() in ["unknown", "unclassified"] or code.lower() in ["unknown", "unclassified"]:
                    raise ValueError(f"Found forbidden label '{label}' at row {row_num}")
                
                valid_label = SchemaValidator.validate_label(label)
                valid_code = SchemaValidator.get_label_code(valid_label)
                
                if str(valid_code) != str(code):
                    raise ValueError(f"Label code mismatch at row {row_num}. Expected {valid_code} for {label}, found {code}")
                    
                # Validate Bounding Box Constraints
                bbox = [float(row["xmin"]), float(row["ymin"]), float(row["xmax"]), float(row["ymax"])]
                if not SchemaValidator.validate_bbox(bbox):
                    raise ValueError(f"Invalid bounding box at row {row_num}: {bbox}")
                
                valid_rows += 1
            except Exception as e:
                logging.warning(f"Validation error in row {row_num}: {e}")
                error_rows += 1
                
    logging.info(f"Validation complete. Valid rows: {valid_rows}, Error rows: {error_rows}")
    
    if error_rows > 0:
        logging.error("Dataset validation failed due to errors. Training cannot proceed.")
        return False
        
    logging.info("Dataset validation passed successfully. Ready for training.")
    return True

def prepare_for_training(csv_path: str, image_dir: str, output_manifest: str):
    """
    Creates a synchronized training manifest after strict validation.
    """
    if not validate_csv(csv_path):
        raise RuntimeError("Dataset validation failed. Fix dataset errors before training.")
        
    logging.info(f"Generating training manifest at {output_manifest}")
    
    # Generate manifest logic...
    with open(output_manifest, 'w') as f:
        f.write(f"Manifest for Grounding DINO Pipeline\n")
        f.write(f"Dataset CSV: {csv_path}\n")
        f.write(f"Image Dir: {image_dir}\n")
        
    logging.info("Training preparation complete.")