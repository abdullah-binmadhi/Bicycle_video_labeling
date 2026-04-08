import re

with open('desktop-app/src/renderer.js', 'r') as f:
    text = f.read()

# Replace metrics updating logic that referenced removed charts
geoMap_pattern = re.compile(
    r'(            // Update Confusion Matrix if available).*?(            showToast\(\'Metrics loaded & parsed successfully!\', \'success\'\);)',
    re.DOTALL
)

def repl_geomap(match):
    return "            // Charts were removed per user request.\n" + match.group(2)

text = geoMap_pattern.sub(repl_geomap, text)

# Replace Misclassification Review Queue logic
misc_pattern = re.compile(
    r'        // Mock Misclassification Review Queue\s*const tbody = document\.getElementById\(\'misclassification-tbody\'\);\s*if \(tbody\) \{.*?\}\s*\}',
    re.DOTALL
)

text = misc_pattern.sub('', text)

with open('desktop-app/src/renderer.js', 'w') as f:
    f.write(text)
print("JavaScript metrics loader wiped for removed charts.")
