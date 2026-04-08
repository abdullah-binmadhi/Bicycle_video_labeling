import re
import os

renderer_path = 'desktop-app/src/renderer.js'
with open(renderer_path, 'r') as f:
    r_content = f.read()

r_old = '''            "Other Road Users": ["bicycle", "pedestrian", "dog", "cat", "squirrel", "motorcycle", "bus", "scooter"],
            "Uncategorized": [] // Fallback
        };

        const categorizedClasses = {};
        for (const cat in categories) categorizedClasses[cat] = [];

        targetClasses.forEach(cls => {
            const clsName = cls.split(' - ')[1] || cls;
            let matched = false;
            for (const [catName, keywords] of Object.entries(categories)) {
                if (catName === "Uncategorized") continue;
                if (keywords.some(kw => clsName.toLowerCase().includes(kw))) {
                    categorizedClasses[catName].push(cls);
                    matched = true;
                    break;
                }
            }
            if (!matched) categorizedClasses["Uncategorized"].push(cls);'''

r_new = '''            "Other Road Users": ["bicycle", "pedestrian", "dog", "cat", "squirrel", "motorcycle", "bus", "scooter"]
        };

        const categorizedClasses = {};
        for (const cat in categories) categorizedClasses[cat] = [];

        targetClasses.forEach(cls => {
            const clsName = cls.split(' - ')[1] || cls;
            let matched = false;
            for (const [catName, keywords] of Object.entries(categories)) {
                if (keywords.some(kw => clsName.toLowerCase().includes(kw))) {
                    categorizedClasses[catName].push(cls);
                    matched = true;
                    break;
                }
            }
            if (!matched) categorizedClasses["Obstacles & Hazards"].push(cls);'''

if r_old in r_content:
    with open(renderer_path, 'w') as f:
        f.write(r_content.replace(r_old, r_new))
    print("renderer.js patched successfully.")
else:
    print("Could not find renderer.js target text.")

yolo_path = 'data_pipeline/yolo_clip_auto.py'
with open(yolo_path, 'r') as f:
    y_content = f.read()

y_old_1 = '''        # Clean target classes for YOLO's zero-shot NLP engine (e.g. "133 - bicycle_lane" -> "bicycle lane")
        self.yolo_classes = [re.sub(r'^\d+\s*-\s*', '', c).replace('_', ' ') for c in self.target_classes]
        self.yolo.set_classes(self.yolo_classes)
        print(f"[System] YOLO-World active with NLP vocabulary: {self.yolo_classes}")
        
        self.use_clip = use_clip
        if self.use_clip:
            print("[System] Initializing CLIP Foundation Model for Stage-2 Refinement...")
            model_id = "openai/clip-vit-large-patch14"
            self.clip_processor = CLIPProcessor.from_pretrained(model_id)
            self.clip_model = CLIPModel.from_pretrained(model_id).to(self.device)
            # Create highly descriptive prompt branches for the CLIP evaluator
            self.clip_prompts = [
                f"a street view photo showing a {c} on the road surface" for c in self.yolo_classes
            ]'''

y_new_1 = '''        # Clean target classes for YOLO's zero-shot NLP engine (e.g. "133 - bicycle_lane" -> "bicycle lane")
        self.yolo_classes = []
        for c in self.target_classes:
            clean_c = re.sub(r'^\d+\s*-\s*', '', c).replace('_', ' ')
            if "bicycle lane" in clean_c or "bike lane" in clean_c or "bicycle mark" in clean_c or "133" in c:
                clean_c = "red painted bike lane or road with bicycle marking"
            self.yolo_classes.append(clean_c)
            
        self.yolo.set_classes(self.yolo_classes)
        print(f"[System] YOLO-World active with NLP vocabulary: {self.yolo_classes}")
        
        self.use_clip = use_clip
        if self.use_clip:
            print("[System] Initializing CLIP Foundation Model for Stage-2 Refinement...")
            model_id = "openai/clip-vit-large-patch14"
            self.clip_processor = CLIPProcessor.from_pretrained(model_id)
            self.clip_model = CLIPModel.from_pretrained(model_id).to(self.device)
            # Create highly descriptive prompt branches for the CLIP evaluator
            self.clip_prompts = []
            for c in self.yolo_classes:
                if "red painted bike lane" in c:
                    self.clip_prompts.append("a street view photo showing a red painted bike lane, or a bicycle mark on the road surface, bicycle priority lane")
                else:
                    self.clip_prompts.append(f"a street view photo showing a {c} on the road surface")'''

if y_old_1 in y_content:
    y_content = y_content.replace(y_old_1, y_new_1)
else:
    print("Could not find yolo_clip_auto.py target text 1.")

y_old_2 = '''        # Write CSV Header
        with open(csv_path, 'w') as f:
            if self.use_clip:
                f.write("frame,label,confidence,x1,y1,x2,y2,clip_refined_desc,clip_confidence\\n")
            else:
                f.write("frame,label,confidence,x1,y1,x2,y2\\n")'''

y_new_2 = '''        # Write CSV Header
        with open(csv_path, 'w') as f:
            if self.use_clip:
                f.write("frame,label,confidence,x1,y1,x2,y2,distance_m,clip_refined_desc,clip_confidence\\n")
            else:
                f.write("frame,label,confidence,x1,y1,x2,y2,distance_m\\n")'''

if y_old_2 in y_content:
    y_content = y_content.replace(y_old_2, y_new_2)
else:
    print("Could not find yolo_clip_auto.py target text 2.")

y_old_3 = '''                            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                            label = self.target_classes[cls_id]
                            
                            clip_desc = ""
                            clip_conf = 0.0'''

y_new_3 = '''                            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                            label = self.target_classes[cls_id]
                            
                            # Simple mono-distance calculation to surface based on bounding box
                            img_h = img_to_draw.shape[0] if img_to_draw is not None else 1080 
                            horizon_y = img_h / 2.0
                            y_diff = max(1.0, y2 - horizon_y)
                            distance_m = (1.5 * 800) / y_diff
                            if distance_m > 100 or distance_m < 0:
                                distance_m = 100.0
                                
                            clip_desc = ""
                            clip_conf = 0.0'''

if y_old_3 in y_content:
    y_content = y_content.replace(y_old_3, y_new_3)
else:
    print("Could not find yolo_clip_auto.py target text 3.")

y_old_4 = '''                            if img_to_draw is not None:
                                import cv2
                                cv2.rectangle(img_to_draw, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                text_label = f"{label} {conf:.2f}"
                                if self.use_clip and clip_desc:
                                    text_label = f"{clip_desc} {clip_conf:.2f}"
                                cv2.putText(img_to_draw, text_label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                                
                            # Save
                            if self.use_clip:
                                f.write(f"{clean_name},{label},{conf:.3f},{x1},{y1},{x2},{y2},{clip_desc},{clip_conf:.3f}\\n")
                            else:
                                f.write(f"{clean_name},{label},{conf:.3f},{x1},{y1},{x2},{y2}\\n")'''

y_new_4 = '''                            if img_to_draw is not None:
                                import cv2
                                is_surface = any(s in label.lower() for s in ['asphalt', 'gravel', 'cobble', 'lane', 'path', 'road', 'paving', 'macadam'])
                                if is_surface:
                                    overlay = img_to_draw.copy()
                                    cv2.rectangle(overlay, (x1, y1), (x2, y2), (255, 0, 150), -1)
                                    cv2.addWeighted(overlay, 0.3, img_to_draw, 0.7, 0, img_to_draw)
                                    cv2.rectangle(img_to_draw, (x1, y1), (x2, y2), (255, 0, 150), 2)
                                else:
                                    cv2.rectangle(img_to_draw, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                    
                                text_label = f"{label} {conf:.2f} {distance_m:.1f}m"
                                if self.use_clip and clip_desc:
                                    text_label = f"{clip_desc[:20]}.. {clip_conf:.2f} {distance_m:.1f}m"
                                cv2.putText(img_to_draw, text_label, (x1, int(y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                                
                            # Save
                            if self.use_clip:
                                f.write(f"{clean_name},{label},{conf:.3f},{x1},{y1},{x2},{y2},{distance_m:.2f},{clip_desc},{clip_conf:.3f}\\n")
                            else:
                                f.write(f"{clean_name},{label},{conf:.3f},{x1},{y1},{x2},{y2},{distance_m:.2f}\\n")'''

if y_old_4 in y_content:
    y_content = y_content.replace(y_old_4, y_new_4)
else:
    print("Could not find yolo_clip_auto.py target text 4.")

with open(yolo_path, 'w') as f:
    f.write(y_content)
print("yolo_clip_auto.py patched successfully.")
