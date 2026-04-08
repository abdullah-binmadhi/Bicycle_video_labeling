import re

with open('desktop-app/src/renderer.js', 'r') as f:
    content = f.read()

# Match window.getCategory definition
get_cat_pattern = r'window\.getCategory\s*=\s*function\s*\(\s*className\s*\)\s*(.*?\{\s*[^}]*\s*\n\s+//.*?return\s*\'Other\';\n\s*\};)'
match = re.search(get_cat_pattern, content, re.DOTALL)

if match:
    full_def = match.group(0)
    
    # Remove it from its current location
    content = content.replace(full_def, "")
    
    # Prepend it right after window.distanceFilterState = {};
    inject_target = "window.distanceFilterState = {};"
    content = content.replace(inject_target, inject_target + "\n\n" + full_def + "\n")
    
    with open('desktop-app/src/renderer.js', 'w') as f:
        f.write(content)
    print("Fixed getCategory location.")
else:
    # Try more generic match
    get_cat_pattern_2 = r'window\.getCategory\s*=\s*function\(className\)\s*\{[\s\S]*?\n\};'
    match2 = re.search(get_cat_pattern_2, content)
    if match2:
        full_def = match2.group(0)
        content = content.replace(full_def, "")
        inject_target = "window.distanceFilterState = {};"
        content = content.replace(inject_target, inject_target + "\n\n" + full_def + "\n")
        with open('desktop-app/src/renderer.js', 'w') as f:
            f.write(content)
        print("Fixed getCategory location (fallback regex).")
    else:
        print("Could not find getCategory definition")

