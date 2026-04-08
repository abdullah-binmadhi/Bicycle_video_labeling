import re

with open('desktop-app/src/renderer.js', 'r') as f:
    text = f.read()

# Replace global switchView declaration
text = text.replace('function switchView(viewName)', 'window.switchView = function(viewName)')
text = text.replace('const oldSwitchView = window.switchView;', 'const oldSwitchView = window.switchView || function(){};')

with open('desktop-app/src/renderer.js', 'w') as f:
    f.write(text)

