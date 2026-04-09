import re

path = 'desktop-app/src/index.html'
with open(path, 'r') as f:
    text = f.read()

text = text.replace("k].visible=true;", "k].active=true;")
text = text.replace("k].visible=false;", "k].active=false;")

with open(path, 'w') as f:
    f.write(text)
print("index.html patched successfully.")
