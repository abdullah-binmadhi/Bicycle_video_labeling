import re

with open('desktop-app/src/index.html', 'r') as f:
    content = f.read()

# Fix CSS layout specifically on the sidebar titles
content = content.replace('class="menu text-[#888] text-[10px] uppercase px-2 py-1"', 'class="menu-title text-[#888] text-[10px] uppercase px-2 py-1"')

with open('desktop-app/src/index.html', 'w') as f:
    f.write(content)
