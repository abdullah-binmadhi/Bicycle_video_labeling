import sys
import json
import os

file_path = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/data_pipeline/clip_auto_labeler.py"
with open(file_path, "r") as f:
    code = f.read()

import re
pattern = re.compile(r"self.target_classes\s*=\s*\{.*?\}(?=\n\s*(?:\"\"\".*?\"\"\"|#|def|\w))", re.DOTALL)
replacement = """import json
        with open(os.path.join(os.path.dirname(__file__), '../config/labels.json'), 'r') as f:
            self.target_classes = json.load(f)"""
new_code = pattern.sub(replacement, code)

with open(file_path, "w") as f:
    f.write(new_code)
print("done")
