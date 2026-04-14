import re

with open("desktop-app/src/index.html", "r") as f:
    content = f.read()

start_marker = '<div class="flex-1 p-8 overflow-y-auto flex flex-col gap-8">'
end_marker = '</main>'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx)

if start_idx != -1 and end_idx != -1:
    with open("new_html_chunk.html", "r") as nf:
        new_chunk = nf.read()
    
    new_content = content[:start_idx] + new_chunk + "\n      " + content[end_idx:]
    
    with open("desktop-app/src/index.html", "w") as f:
        f.write(new_content)
    print("Replaced content successfully.")
else:
    print("Could not find markers.", start_idx, end_idx)
