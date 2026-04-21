import os
import csv
from pathlib import Path

def convert_csv(input_csv, output_csv, frames_dir):
    if not os.path.exists(input_csv):
        print(f"Error: Could not find {input_csv}")
        return
        
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    
    with open(input_csv, 'r') as infile, open(output_csv, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.writer(outfile)
        
        # Write the new header expected by the desktop app
        writer.writerow(['image_id', 'label_code', 'class_name', 'xmin', 'ymin', 'xmax', 'ymax', 'score'])
        
        converted = 0
        for row in reader:
            frame_name = row['frame']
            # The app expects the absolute or relative path that matches exactly what it loads.
            # But the app also just does a `.indexOf('image_id')` and checks if it matches `imagePath`
            # Wait, `imagePath` in the app is the FULL absolute path of the image on the disk!
            # Let's check renderer.js to see how it matches `image_id`:
            # `if (cols[idxId] !== imagePath) return; // only this image`
            
            # So `image_id` MUST be the full absolute path of the frame.
            full_frame_path = os.path.join(frames_dir, frame_name)
            
            label_raw = row['label']
            label_code = "0"
            if "-" in label_raw:
                parts = label_raw.split("-", 1)
                label_code = parts[0].strip()
                class_name = parts[1].strip()
            else:
                class_name = label_raw
                
            confidence = row['confidence']
            x1 = row['x1']
            y1 = row['y1']
            x2 = row['x2']
            y2 = row['y2']
            
            writer.writerow([full_frame_path, label_code, class_name, x1, y1, x2, y2, confidence])
            converted += 1
            
    print(f"Successfully converted {converted} annotations!")
    print(f"Saved to: {output_csv}")

if __name__ == "__main__":
    base_dir = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/Project Surface Detection/LM-17.06/876ED8BA-AF81-4DCD-9A29-8702D236B21D"
    input_csv = os.path.join(base_dir, "csv and checkpoints", "Label.0.csv")
    frames_dir = os.path.join(base_dir, "Frames")
    output_csv = os.path.join(frames_dir, "master_annotations.csv")
    
    convert_csv(input_csv, output_csv, frames_dir)
