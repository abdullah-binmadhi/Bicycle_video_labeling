import re

with open("/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html", "r") as f:
    lines = f.readlines()

depth = 0
for i, line in enumerate(lines):
    # simple heuristic for opening and closing tags. It's not a full HTML parser, but works for most well-formatted HTML
    # We should count <div...> ignoring self-closing which div never is
    opens = len(re.findall(r'<div[^>]*>', line))
    closes = len(re.findall(r'</div\s*>', line))
    depth += opens - closes
    if depth < 2:
        print(f"L{i+1} [D:{depth} O:{opens} C:{closes}]: {line.strip()}")

