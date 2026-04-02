with open("/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html", "r") as f:
    text = f.read()

import re
pattern = r'<select id="dataset-label-select"[^>]*>.*?<\/select>'
replacement = """<select id="dataset-label-select" class="select select-sm select-bordered border-[#444] bg-black text-[#e0e0e0] rounded-none ml-2">
                 </select>"""
text = re.sub(pattern, replacement, text, flags=re.DOTALL)

with open("/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html", "w") as f:
    f.write(text)

print("Select wiped for dynamic load")
