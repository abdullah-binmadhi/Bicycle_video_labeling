with open("/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html", "r") as f:
    text = f.read()

import re
text = re.sub(r'class="opacity-50 cursor-not-allowed"', r'class="hover:bg-[#444] text-[#e0e0e0]"', text)

with open("/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html", "w") as f:
    f.write(text)

print("Unlocked dropdown options")
