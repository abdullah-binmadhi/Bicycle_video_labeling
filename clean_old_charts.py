import re

with open('desktop-app/src/renderer.js', 'r') as f:
    text = f.read()

# Delete Per-Class Accuracy initialization
classBar_regex = re.compile(r'    if\(ctxClassBar && !classBarChart\).*?\}\s*\);\s*\}', re.DOTALL)
text = classBar_regex.sub('    // Removed classBarChart initialization', text)

# Delete Loss Convergence initialization
conv_regex = re.compile(r'    // 3\. Loss Convergence Curve\s*const ctxConv = document\.getElementById.*?\}\s*\);\s*\}', re.DOTALL)
text = conv_regex.sub('    // Removed convergenceChart initialization', text)

# Just in case Confusion Matrix is still there...
conf_regex = re.compile(r'    // 1\. Confusion Matrix.*?\}\s*\);\s*\}', re.DOTALL)
text = conf_regex.sub('    // Removed confChart initialization', text)

with open('desktop-app/src/renderer.js', 'w') as f:
    f.write(text)

