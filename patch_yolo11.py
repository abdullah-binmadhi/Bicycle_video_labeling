import re
filepath = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/data_pipeline/yolo_clip_auto.py"
with open(filepath, 'r') as f:
    content = f.read()

# 1. Import YOLO instead of YOLOWorld
content = content.replace("from ultralytics import YOLOWorld", "from ultralytics import YOLO")

# 2. Change default model to yolo11x.pt
content = content.replace("default='yolov8x-world.pt'", "default='yolo11x.pt'")

# 3. Inject YOLO logic inside TwoStageAnnotator.__init__
init_old = """    def __init__(self, target_classes, use_clip=False, model="yolov8x-world.pt", conf=0.25):
        self.conf = conf
        self.device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
        
        print(f"\\n[System] Initializing YOLO-World ({model})...")
        # Using YOLO-World for open-vocabulary zero-shot detection
        self.yolo = YOLOWorld(model) # Initialize the chosen model weight
        
        # Inject the custom target vocabulary into YOLO
        self.target_classes = target_classes
        
        # Split target classes into YOLO objects vs CLIP surface textures
        self.yolo_classes = []
        self.yolo_original_labels = []
        self.surface_classes = []
        self.surface_original_labels = []"""

init_new = """    def __init__(self, target_classes, use_clip=False, model="yolo11x.pt", conf=0.25):
        self.conf = conf
        self.device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
        
        print(f"\\n[System] Initializing Standard YOLO ({model})...")
        self.yolo = YOLO(model)
        
        self.target_classes = target_classes
        
        coco_mapping = {
            "person": 0, "pedestrian": 0,
            "bicycle": 1, "bike": 1,
            "car": 2, "automobile": 2,
            "motorcycle": 3, "motorbike": 3,
            "bus": 5, "truck": 7, "lorry": 7,
            "traffic light": 9, "stop sign": 11
        }
        self.coco_mapping = coco_mapping
        
        self.yolo_classes = []
        self.yolo_ids = []
        self.yolo_original_labels = []
        self.surface_classes = []
        self.surface_original_labels = []"""

content = content.replace(init_old, init_new)

# 4. Modify how classes are appended in __init__
append_old = """            if is_surface:
                self.surface_classes.append(clean_c)
                self.surface_original_labels.append(c)
            else:
                self.yolo_classes.append(clean_c)
                self.yolo_original_labels.append(c)
            
        if self.yolo_classes:
            self.yolo.set_classes(self.yolo_classes)
        print(f"[System] YOLO-World active with Object vocabulary: {self.yolo_classes}")"""

append_new = """            matched_id = None
            for k, v in self.coco_mapping.items():
                if k in clean_c:
                    matched_id = v
                    break
            
            if matched_id is not None and not is_surface:
                self.yolo_classes.append(clean_c)
                self.yolo_ids.append(matched_id)
                self.yolo_original_labels.append(c)
            else:
                self.surface_classes.append(clean_c)
                self.surface_original_labels.append(c)
                
        print(f"[System] YOLO COCO Object classes active: {list(zip(self.yolo_classes, self.yolo_ids))}")"""

content = content.replace(append_old, append_new)

# 5. Modify YOLO predict loop logic
pred_old = """                        for r in results:
                            boxes = r.boxes
                            for box in boxes:
                                cls_id = int(box.cls[0].item())
                                conf = float(box.conf[0].item())
                                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                                label = self.yolo_original_labels[cls_id]"""

pred_new = """                        for r in results:
                            boxes = r.boxes
                            for box in boxes:
                                cls_id = int(box.cls[0].item())
                                
                                # Only process object if it's in our requested target IDs
                                if cls_id not in self.yolo_ids:
                                    continue
                                    
                                idx_in_labels = self.yolo_ids.index(cls_id)
                                label = self.yolo_original_labels[idx_in_labels]
                                conf = float(box.conf[0].item())
                                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())"""

content = content.replace(pred_old, pred_new)

# 6. Update clip fallbacks
content = content.replace("clip_desc = self.clip_prompts[cls_id]", "clip_desc = self.clip_prompts[idx_in_labels]")

with open(filepath, 'w') as f:
    f.write(content)
print("Patch successful!")
