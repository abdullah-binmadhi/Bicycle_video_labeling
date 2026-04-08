import re

with open('desktop-app/src/index.html', 'r') as f:
    content = f.read()

print("Checking sidebar menu items...")
for match in re.findall(r'<li class="[^"]*".*?</li>', content)[:5]:
    print(match)

