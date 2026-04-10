import sys
import os
import csv
import logging
sys.path.insert(0, os.path.abspath('src'))
from pipeline.schema import SchemaValidator
from pipeline.annotator import GroundingDinoAnnotator
from pipeline.trainer import validate_csv, prepare_for_training

logging.basicConfig(level=logging.INFO)

# Test SchemaValidator
def test_schema():
    assert SchemaValidator.validate_label("car") == "car"
    assert SchemaValidator.validate_label("  CaR  ") == "car"
    assert SchemaValidator.get_label_code("car") == "3"
    assert SchemaValidator.get_label_code("3") == "3"
    
    try:
        SchemaValidator.validate_label("unknown")
        assert False, "Should have raised exception"
    except ValueError:
        pass
        
    assert SchemaValidator.validate_bbox([0.1, 0.1, 0.9, 0.9])
    assert not SchemaValidator.validate_bbox([0.9, 0.9, 0.1, 0.1])
    
    preds = [
        {"label": "car", "box": [0.1, 0.1, 0.5, 0.5], "score": 0.9},
        {"label": "unknown", "box": [0.1, 0.1, 0.5, 0.5], "score": 0.9},
        {"label": "person", "box": [0.9, 0.9, 0.1, 0.1], "score": 0.9}
    ]
    processed = SchemaValidator.process_predictions(preds)
    assert len(processed) == 1
    assert processed[0]["label_code"] == "3"
    assert processed[0]["class_name"] == "car"
    print("Schema tests passed!")

test_schema()

def test_annotator():
    # Make dummy image dir
    os.makedirs('dummy_imgs', exist_ok=True)
    with open('dummy_imgs/test1.jpg', 'w') as f: f.write('dummy')
    
    annotator = GroundingDinoAnnotator(config_path="dummy", weights_path="dummy", device="cpu")
    annotator.process_dataset('dummy_imgs', 'dummy_output.csv')
    
    with open('dummy_output.csv', 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) > 0
        assert rows[0]['class_name'] == 'car'
        assert rows[0]['label_code'] == '3'
    print("Annotator tests passed!")

test_annotator()

def test_trainer():
    # Valid CSV
    assert validate_csv('dummy_output.csv') == True
    
    # Invalid CSV
    with open('invalid.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["image_id", "label_code", "class_name", "xmin", "ymin", "xmax", "ymax", "score"])
        writer.writeheader()
        writer.writerow({
            "image_id": "test", "label_code": "unknown", "class_name": "unknown",
            "xmin": 0, "ymin": 0, "xmax": 1, "ymax": 1, "score": 0.9
        })
        
    assert validate_csv('invalid.csv') == False
    
    # Run full prep
    prepare_for_training('dummy_output.csv', 'dummy_imgs', 'dummy_manifest.txt')
    assert os.path.exists('dummy_manifest.txt')
    print("Trainer tests passed!")

test_trainer()
