import os
import ultralytics
from ultralytics import settings

print("Ultralytics settings:")
print(settings)
print(f"\nweights_dir: {settings.get('weights_dir')}")

print("\nEnvironment Variables:")
print(f"YOLO_CONFIG_DIR: {os.environ.get('YOLO_CONFIG_DIR')}")
