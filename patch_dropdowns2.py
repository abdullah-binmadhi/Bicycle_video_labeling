import re

with open('desktop-app/src/renderer.js', 'r') as f:
    content = f.read()

# 1. Provide a massive mocked trainingDataRaw
mock_data_script = """
window.trainingDataRaw = {
    labels: window.defaultClasses,
    tp: window.defaultClasses.map(() => Math.floor(Math.random() * 80) + 20),
    fn: window.defaultClasses.map(() => Math.floor(Math.random() * 30)),
    acc: window.defaultClasses.map(() => Math.floor(Math.random() * 40) + 60),
    classTotals: window.defaultClasses.map(() => Math.floor(Math.random() * 1000) + 100)
};
window.trainingFilterState = {};
window.distanceFilterState = {};

window.renderDistanceFilter = function() {
    const container = document.getElementById('distance-filter-dropdown');
    if (!container) return;
    container.innerHTML = '';
    
    const roadSurfaces = window.defaultClasses.filter(lbl => window.getCategory(lbl) === 'Surfaces');
    
    roadSurfaces.forEach(lbl => {
        if (window.distanceFilterState[lbl] === undefined) {
            window.distanceFilterState[lbl] = false;
        }
        
        const wrapper = document.createElement('label');
        wrapper.className = 'flex items-center gap-2 mb-1 p-1 hover:bg-[#222] cursor-pointer rounded';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'w-3 h-3 rounded bg-gray-700 border-gray-600 text-blue-500 cursor-pointer';
        checkbox.checked = window.distanceFilterState[lbl];
        checkbox.onchange = (e) => {
            window.distanceFilterState[lbl] = e.target.checked;
            window.updateMapState(); // map state updates the distance chart
        };
        const text = document.createElement('span');
        text.className = 'text-[10px] uppercase font-mono text-gray-300';
        text.innerText = lbl;
        wrapper.appendChild(checkbox);
        wrapper.appendChild(text);
        container.appendChild(wrapper);
    });
};
"""

# Replace the current trainingDataRaw block
content = re.sub(
    r'window\.trainingDataRaw\s*=\s*\{.*?\};\s*window\.trainingFilterState\s*=\s*\{\};',
    mock_data_script.replace('\\', '\\\\'),
    content,
    flags=re.DOTALL
)

# 2. Update renderTrainingFilter defaults
content = re.sub(
    r'if\s*\(\s*window\.trainingFilterState\[lbl\]\s*===\s*undefined\s*\)\s*\{\s*window\.trainingFilterState\[lbl\]\s*=\s*true;\s*\}',
    r'if (window.trainingFilterState[lbl] === undefined) { window.trainingFilterState[lbl] = false; }',
    content
)

with open('desktop-app/src/renderer.js', 'w') as f:
    f.write(content)
print("done replacing.")
