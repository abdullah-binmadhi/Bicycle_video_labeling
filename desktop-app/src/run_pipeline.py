import os
import argparse
import logging
from pipeline.annotator import GroundingDinoAnnotator
from pipeline.trainer import prepare_for_training

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_args():
    parser = argparse.ArgumentParser(description="End-to-End ML Pipeline for Grounding DINO Annotation and Training")
    parser.add_argument("--image-dir", required=True, help="Path to input images directory")
    parser.add_argument("--output-csv", default="dataset.csv", help="Output CSV path for annotations")
    parser.add_argument("--manifest-dir", default="manifests/", help="Directory to save training manifests")
    parser.add_argument("--config", default="groundingdino/config/GroundingDINO_SwinT_OGC.py", help="Grounding DINO config path")
    parser.add_argument("--weights", default="weights/groundingdino_swint_ogc.pth", help="Grounding DINO weights path")
    parser.add_argument("--device", default="cpu", help="Device to run inference on (cpu, cuda)")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # 1. Pipeline Initialization & Auto-Annotation
    logging.info("Starting Grounding DINO auto-annotation pipeline...")
    annotator = GroundingDinoAnnotator(
        config_path=args.config,
        weights_path=args.weights,
        device=args.device
    )
    
    # Process dataset (includes inline schema validation & error handling)
    annotator.process_dataset(args.image_dir, args.output_csv)
    
    # 2. Pipeline Synchronization & Training Preparation
    logging.info("Starting dataset validation and training preparation...")
    os.makedirs(args.manifest_dir, exist_ok=True)
    manifest_path = os.path.join(args.manifest_dir, "train_manifest.txt")
    
    try:
        # Enforce strict validation to eliminate unknown/unclassified labels
        prepare_for_training(args.output_csv, args.image_dir, manifest_path)
        logging.info("End-to-End pipeline completed successfully. Ready for ML training.")
    except Exception as e:
        logging.error(f"Pipeline failed during validation: {e}")
        exit(1)

if __name__ == "__main__":
    main()