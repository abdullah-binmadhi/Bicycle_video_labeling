import argparse
from ultralytics import YOLO

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset_yaml', required=True)
    parser.add_argument('--epochs', type=int, default=50)
    args = parser.parse_args()
    
    print(f"[System] Starting Custom YOLOv11 Training on {args.dataset_yaml}...")
    model = YOLO('yolo11n.pt')
    model.train(data=args.dataset_yaml, epochs=args.epochs, imgsz=640)
    print("[System] Training complete! weights saved in runs/detect/train/weights")

if __name__ == '__main__':
    main()
