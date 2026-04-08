import re

with open('desktop-app/src/renderer.js', 'r') as f:
    text = f.read()

# Remove the window.trainingDataRaw, window.trainingFilterState, and window.renderTrainingFilter definitions
text = re.sub(
    r'window\.trainingDataRaw\s*=\s*\{.*?\};\s*window\.trainingFilterState\s*=\s*\{\};',
    '',
    text,
    flags=re.DOTALL
)

text = re.sub(
    r'window\.renderTrainingFilter\s*=\s*function\(\)\s*\{.*?\n};\s*',
    '',
    text,
    flags=re.DOTALL
)

text = re.sub(
    r'window\.updateTrainingCharts\s*=\s*function\(\)\s*\{.*?\n};\s*',
    '',
    text,
    flags=re.DOTALL
)

# In initAnalytics(), we want to strip the charts setup.
# Find the start of initAnalytics() to the Geospatial Map.

initAnalytics_pattern = re.compile(
    r'function initAnalytics\(\)\s*\{.*?// 6\. Geospatial Map',
    re.DOTALL
)

def repl_init(match):
    # Just keep the "distance-canvas" logic which we still need.
    return """function initAnalytics() {
    // 5.5 Distance Distribution Bar Chart
    const ctxDistBar = document.getElementById('distance-canvas');
    if(ctxDistBar && !distanceChart) {
        distanceChart = new Chart(ctxDistBar, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Total Distance per Surface (m)',
                    data: [],
                    backgroundColor: [],
                    borderWidth: 0
                }]
            },
            options: { 
                responsive: true, 
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: 'rgba(255,255,255,0.7)', font: { family: 'monospace' } },
                        grid: { color: 'rgba(255,255,255,0.1)' }
                    },
                    x: {
                        ticks: { color: 'rgba(255,255,255,0.7)', font: { family: 'monospace', size: 10 } },
                        grid: { display: false }
                    }
                },
                plugins: { legend: { display: false } }
             }
        });
    }
    
    // UI initializations for Filters
    window.renderDistanceFilter();

    // 6. Geospatial Map"""

text = initAnalytics_pattern.sub(repl_init, text)

# Now, we need to remove the mock data loops from the Geospatial Map section
geoMap_pattern = re.compile(
    r'(geoLayerGroup = L\.layerGroup\(\)\.addTo\(analyticsMap\);).*?window\.classState = \{\};',
    re.DOTALL
)

def repl_geoMap(match):
    return match.group(1) + """
        
        // No mock data generated here. Waiting for CSV/Scraper load.
        window.classState = {};"""

text = geoMap_pattern.sub(repl_geoMap, text)

# Also remove the second mock data loop and the chart update at the end of initAnalytics
# from `window.classState[surface] = { ... } };` to `setTimeout(() => analyticsMap.invalidateSize(), 300);`
second_loop_pattern = re.compile(
    r'(window\.classState\[surface\] = \{\s*visible: false,\s*color: defColor\s*\};\s*\}\s*\};\s*)for\s*\(let i = 0; i < 50; i\+\+\).*?(\/\/\s*Force Leaflet to recalculate)',
    re.DOTALL
)

def repl_second_loop(match):
    return match.group(1) + match.group(2)

text = second_loop_pattern.sub(repl_second_loop, text)

# Remove `window.updateTrainingCharts();` from switchView
text = re.sub(
    r'if \(typeof window\.updateTrainingCharts === \'function\'\) \{\s*window\.updateTrainingCharts\(\);\s*\}',
    '',
    text
)

# Ensure chart variables only declare the ones we need
text = re.sub(
    r'let confChart = null, classBarChart = null, convergenceChart = null, stabilityChart = null, distributionChart = null, distanceChart = null;',
    r'let distanceChart = null;',
    text
)

with open('desktop-app/src/renderer.js', 'w') as f:
    f.write(text)
print("JavaScript charts and mock loops wiped out.")
