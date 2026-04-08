import re

with open('desktop-app/src/renderer.js', 'r') as f:
    content = f.read()

fixed = content.replace("        }\n        \n\n};\n", "        }\n    }\n};\n")

with open('desktop-app/src/renderer.js', 'w') as f:
    f.write(fixed)
