import re

readme = "README.md"
with open(readme, 'r') as f:
    text = f.read()

# Update python dependencies
old_text = "Python 3.9+ (if you are running the ML pipeline components)"
new_text = "Python 3.9+ (if you are running the ML pipeline components)\\n- `pip install ultralytics transformers torch torchvision opencv-python Pillow`"

if new_text not in text:
    text = text.replace(old_text, new_text)
    
with open(readme, 'w') as f:
    f.write(text)
print("Updated README")
