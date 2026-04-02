import os
import argparse
import sys
from roboflow import Roboflow

def main():
    parser = argparse.ArgumentParser(description="Roboflow Pipeline Manager")
    parser.add_argument("--mode", required=True, choices=["upload", "download", "inference"], help="Mode of operation")
    parser.add_argument("--api_key", required=True, help="Roboflow API Key")
    parser.add_argument("--workspace", required=True, help="Roboflow Workspace ID")
    parser.add_argument("--project", required=True, help="Roboflow Project ID")
    parser.add_argument("--version", type=int, default=1, help="Dataset version (for download/inference)")
    parser.add_argument("--input", type=str, help="Input directory (for upload) or file (for inference)")
    parser.add_argument("--output", type=str, default=".", help="Output directory (for download)")

    args = parser.parse_args()

    print(f"Initializing Roboflow SDK (Mode: {args.mode})...")
    
    try:
        rf = Roboflow(api_key=args.api_key)
        workspace = rf.workspace(args.workspace)
        project = workspace.project(args.project)
    except Exception as e:
        print(f"Error authenticating with Roboflow: {e}")
        sys.exit(1)

    if args.mode == "upload":
        if not args.input or not os.path.isdir(args.input):
            print("Error: For upload mode, --input must be a valid directory containing images.")
            sys.exit(1)
            
        print(f"Uploading frames from {args.input} to {args.workspace}/{args.project}...")
        image_extensions = ('.png', '.jpg', '.jpeg')
        files = [f for f in os.listdir(args.input) if f.lower().endswith(image_extensions)]
        count = 0
        total = len(files)
        
        if total == 0:
            print("No images found in the input directory.")
            sys.exit(0)
            
        for img in files:
            img_path = os.path.join(args.input, img)
            try:
                # Upload method according to roboflow SDK
                project.upload(img_path)
                count += 1
                if count % 10 == 0:
                    print(f"Uploaded {count}/{total} images...")
            except Exception as e:
                print(f"Failed to upload {img}: {e}")
                
        print(f"Upload complete! Successfully uploaded {count} out of {total} images.")

    elif args.mode == "download":
        version = project.version(args.version)
        print(f"Downloading dataset {args.workspace}/{args.project} (Version {args.version}) to {args.output}...")
        try:
            # Download dataset in YOLO format (can be changed to other formats)
            dataset = version.download("yolov8", location=args.output)
            print(f"Dataset successfully downloaded to: {dataset.location}")
        except Exception as e:
            print(f"Error downloading dataset: {e}")
            sys.exit(1)

    elif args.mode == "inference":
        if not args.input or not os.path.exists(args.input):
            print("Error: For inference mode, --input must be a valid image file.")
            sys.exit(1)
            
        version = project.version(args.version)
        print(f"Running inference on {args.input} using model {args.workspace}/{args.project} (Version {args.version})...")
        try:
            model = version.model
            prediction = model.predict(args.input)
            
            # Print predictions in a nice format
            print(f"\\n--- Inference Results ---")
            print(prediction.json())
            
            # Optionally save an annotated image alongside the original
            output_path = os.path.join(os.path.dirname(args.input), f"pred_{os.path.basename(args.input)}")
            prediction.save(output_path)
            print(f"Annotated image saved at: {output_path}")
            
        except Exception as e:
            print(f"Error during inference: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
