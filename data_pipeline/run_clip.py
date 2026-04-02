import os
import argparse
from pathlib import Path
import sys

# Add the directory to path so we can import the module correctly
pipeline_dir = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/data_pipeline"
sys.path.append(pipeline_dir)

try:
    from clip_annotator import ZeroShotAnnotator
except ImportError as e:
    print(f"Error importing annotator: {e}")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Zero-shot video frame annotation using CLIP.")
    parser.add_argument("--frames_dir", type=str, required=True, help="Path to extracted video frames")
    parser.add_argument("--output_csv", type=str, required=True, help="Path to save output labels (e.g. Label.csv)")
    
    args = parser.parse_args()
    
    frames_path = Path(args.frames_dir)
    out_csv_path = Path(args.output_csv)
    
    if not frames_path.exists():
        print(f"Error: Frames directory not found at {frames_path}")
        sys.exit(1)
        
    out_csv_path.parent.mkdir(parents=True, exist_ok=True)
        
    print(f"Loading CLIP Annotator...")
    annotator = ZeroShotAnnotator()
    
    print(f"Processing frames from: {frames_path}")
    print(f"Saving annotations to: {out_csv_path}")
    
    try:
        annotator.annotate_session(frames_path, out_csv_path)
        print("\nSuccess! CLIP zero-shot annotation complete.")
    except Exception as e:
        print(f"\nError during annotation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
