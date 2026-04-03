js_path = 'data_pipeline/yolo_clip_auto.py'
with open(js_path, 'r', encoding='utf-8') as f:
    code = f.read()

import re

# Update argparse
old_args = """def parse_args():
    parser = argparse.ArgumentParser(description="Multi-Stage Auto Annotation")
    parser.add_argument('--classes', nargs='+', help='Target YOLO classes to detect', default=["bicycle", "car", "pedestrian", "pothole"])
    parser.add_argument('--out', type=str, default='data_pipeline/labeled_data', help='Output folder')
    parser.add_argument('--use_clip', action='store_true', help='Pass YOLO crops to CLIP for zero-shot description')
    return parser.parse_args()"""

new_args = """def parse_args():
    parser = argparse.ArgumentParser(description="Multi-Stage Auto Annotation")
    parser.add_argument('--frames_dir', type=str, help='Path to extracted frame images', required=True)
    parser.add_argument('--output_csv', type=str, help='Path to save output CSV file', required=True)
    parser.add_argument('--classes', nargs='+', help='Target YOLO classes to detect', default=["bicycle", "car", "pedestrian", "pothole"])
    parser.add_argument('--out', type=str, default='', help='Ignore')
    parser.add_argument('--use_clip', action='store_true', help='Pass YOLO crops to CLIP for zero-shot description')
    return parser.parse_args()"""

code = code.replace(old_args, new_args)

# Fix Run signature
old_run = """    def run(self, input_dir, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        csv_path = os.path.join(output_dir, "auto_annotations.csv")"""

new_run = """    def run(self, input_dir, csv_path):
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)"""

code = code.replace(old_run, new_run)

# Fix Main execution
old_main = """if __name__ == "__main__":
    args = parse_args()
    
    # We grab input frames statically from standard extraction path if no --input arg
    # Actually, our UI doesn't pass input path directly unless modified, let's assume default
    # Looking at data pipeline context...
    input_dir = "extracted_frames"
    # Actually just passing it hardcoded or searching for extracted frames
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_frames = os.path.join(base_dir, 'data_pipeline', 'extracted_frames')
    if not os.path.exists(target_frames):
         target_frames = os.path.join(base_dir, 'extracted_frames')
    
    print(f"Reading frames from: {target_frames}")
    
    annotator = TwoStageAnnotator(target_classes=args.classes, use_clip=args.use_clip)
    annotator.run(target_frames, args.out)"""

new_main = """if __name__ == "__main__":
    args = parse_args()
    print(f"Reading frames from: {args.frames_dir}")
    annotator = TwoStageAnnotator(target_classes=args.classes, use_clip=args.use_clip)
    annotator.run(args.frames_dir, args.output_csv)"""

code = code.replace(old_main, new_main)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(code)
print("Updated python arguments successfully")
