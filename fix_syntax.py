import re

with open('desktop-app/src/renderer.js', 'r') as f:
    text = f.read()

# Fix syntax error caused by regex botch
text = re.sub(r'window\.classState\[l\] && window\.classState\[l\]\.color\) \? window\.classState\[l\]\.color : \'#555\'\);\n\n        if \(window\.distanceChartInstance\)', '        if (window.distanceChartInstance)', text)

with open('desktop-app/src/renderer.js', 'w') as f:
    f.write(text)
