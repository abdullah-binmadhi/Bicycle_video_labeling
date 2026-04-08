with open('desktop-app/src/renderer.js', 'r') as f:
    content = f.read()

old_logic = """
        if (isVisible) {
            // Aggregate distance
            if (!distanceAgg[s]) distanceAgg[s] = 0;
            distanceAgg[s] += dist;
"""

new_logic = """
        // Aggregate distance ALWAYS so dropdown filter works independently of map visibility
        if (!distanceAgg[s]) distanceAgg[s] = 0;
        distanceAgg[s] += dist;

        if (isVisible) {
"""

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    with open('desktop-app/src/renderer.js', 'w') as f:
        f.write(content)
    print("Fixed distanceAgg logic.")
else:
    print("Could not find old_logic. Let's try Regex.")
    import re
    old_logic_re = r'if\s*\(\s*isVisible\s*\)\s*\{\s*// Aggregate distance\s*if\s*\(\!distanceAgg\[s\]\)\s*distanceAgg\[s\]\s*=\s*0;\s*distanceAgg\[s\]\s*\+=\s*dist;'
    new_logic_re = r'''// Aggregate distance
        if (!distanceAgg[s]) distanceAgg[s] = 0;
        distanceAgg[s] += dist;

        if (isVisible) {'''
    content = re.sub(old_logic_re, new_logic_re, content)
    with open('desktop-app/src/renderer.js', 'w') as f:
        f.write(content)
    print("Used Regex to fix distanceAgg logic.")
