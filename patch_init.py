import re

with open('desktop-app/src/renderer.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update initAnalytics to call the filters correctly
init_match = r'''    // 4\. Temporal Stability \(Flicker\)
    const ctxStab = document\.getElementById\('stability-canvas'\);'''

init_sub = '''    // UI initializations for Filters
    window.renderTrainingFilter();
    window.renderDistanceFilter();

    // 4. Temporal Stability (Flicker)
    const ctxStab = document.getElementById('stability-canvas');'''

content = re.sub(init_match, init_sub, content)

with open('desktop-app/src/renderer.js', 'w', encoding='utf-8') as f:
    f.write(content)

