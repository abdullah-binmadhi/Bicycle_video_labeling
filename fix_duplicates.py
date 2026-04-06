import re

with open("desktop-app/src/renderer.js", "r") as f:
    content = f.read()

# Find the first occurrence
init_marker = "window.currentGeoData = [];\nwindow.classState = {};"

parts = content.split(init_marker)
if len(parts) > 2:
    # Multiple occurrences found
    # Keep the first one intact with its block, but subsequent ones must have their block removed.
    
    # We know that the block ends with the def of `window.registerSurface` and `};`
    # Let's extract the exact block string from the first occurrence by looking for the next code line...
    # This might be tricky. Let's just remove the block entirely from all occurrences but the uppermost global scope one! Wait, where was the original global scope window.currentGeoData?
