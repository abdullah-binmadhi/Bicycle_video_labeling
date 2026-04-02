import re

with open("/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html", "r") as f:
    lines = f.readlines()

depth = 0
for i, line in enumerate(lines):
    opens = len(re.findall(r'<div\b[^>]*>', line))
    closes = len(re.findall(r'</div>', line))
    depth += opens - closes
    if i+1 >= 405 and i+1 <= 425:
        print(f"Line {i+1}: opens={opens}, closes={closes}, depth={depth} | {line.strip()}")
