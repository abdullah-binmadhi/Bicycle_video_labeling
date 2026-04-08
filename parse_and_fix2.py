import re

with open('desktop-app/src/renderer.js', 'r') as f:
    text = f.read()

# Delete stabilityChart initialization
stab_regex = re.compile(r'const ctxStab = document\.getElementById.*?\}\s*\);\s*\}', re.DOTALL)
text = stab_regex.sub('// Removed stabilityChart initialization', text)

# Delete distributionChart initialization
dist_regex = re.compile(r'// 5\. Data Distribution.*?(?=// 6\. Geospatial Map)', re.DOTALL)
text = dist_regex.sub('', text)

# Remove the synthetic map data generation
mock_regex = re.compile(r'// Generate synthetic initial map data.*?(?=// Force Leaflet to recalculate)', re.DOTALL)
text = mock_regex.sub('// No mock data generated here. Waiting for CSV/Scraper load.\n        window.classState = {};\n', text)

with open('desktop-app/src/renderer.js', 'w') as f:
    f.write(text)

