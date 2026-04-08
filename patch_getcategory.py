import re

with open('desktop-app/src/renderer.js', 'r') as f:
    text = f.read()

text = text.replace(
    'window.getCategory = function(className) {',
    "window.getCategory = function(className) {\n    if (!className) return 'Other';"
)

with open('desktop-app/src/renderer.js', 'w') as f:
    f.write(text)
