import re

with open('desktop-app/src/renderer.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. State and Helper for Training Charts Filter

training_js = '''// --- Advanced UI Filtering ---
window.trainingDataRaw = {
    labels: ['134 - asphalt', '8 - gravel', '19 - cobblestone', '1 - potholes', '5 - speed_bump', '133 - bicycle_lane', '18 - rail_tracks'],
    tp: [98, 85, 92, 76, 50, 89, 45],
    fn: [2, 15, 8, 24, 3, 4, 10],
    acc: [98, 85, 92, 76, 50, 89, 45], // mocked initially
    classTotals: [1500, 800, 450, 200, 100, 150, 300]
};
window.trainingFilterState = {};

window.renderTrainingFilter = function() {
    const container = document.getElementById('training-filter-dropdown');
    if (!container) return;
    container.innerHTML = '';
    
    window.trainingDataRaw.labels.forEach((lbl, idx) => {
        if (window.trainingFilterState[lbl] === undefined) {
            window.trainingFilterState[lbl] = true;
        }
        
        const wrapper = document.createElement('label');
        wrapper.className = 'flex items-center gap-2 mb-1 p-1 hover:bg-[#222] cursor-pointer rounded';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'w-3 h-3 rounded bg-gray-700 border-gray-600 text-emerald-500 cursor-pointer';
        checkbox.checked = window.trainingFilterState[lbl];
        checkbox.onchange = (e) => {
            window.trainingFilterState[lbl] = e.target.checked;
            window.updateTrainingCharts();
        };
        const text = document.createElement('span');
        text.className = 'text-[10px] uppercase font-mono text-gray-300';
        text.innerText = lbl;
        wrapper.appendChild(checkbox);
        wrapper.appendChild(text);
        container.appendChild(wrapper);
    });
};

window.updateTrainingCharts = function() {
    if (!confChart || !classBarChart || !distributionChart) return;
    
    const fLabels = [];
    const fTp = [];
    const fFn = [];
    const fAcc = [];
    const fTotals = [];
    const fColors = [];
    
    const colorBank = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#a855f7', '#2dd4bf', '#64748b'];
    
    window.trainingDataRaw.labels.forEach((lbl, idx) => {
        if (window.trainingFilterState[lbl]) {
            fLabels.push(lbl);
            fTp.push(window.trainingDataRaw.tp[idx] || 0);
            fFn.push(window.trainingDataRaw.fn[idx] || 0);
            fAcc.push(window.trainingDataRaw.acc[idx] || 0);
            fTotals.push(window.trainingDataRaw.classTotals[idx] || 0);
            fColors.push(colorBank[idx % colorBank.length]);
        }
    });
    
    confChart.data.labels = fLabels;
    confChart.data.datasets[0].data = fTp;
    confChart.data.datasets[1].data = fFn;
    confChart.update();
    
    classBarChart.data.labels = fLabels;
    classBarChart.data.datasets[0].data = fAcc;
    classBarChart.update();
    
    distributionChart.data.labels = fLabels;
    distributionChart.data.datasets[0].data = fTotals;
    distributionChart.data.datasets[0].backgroundColor = fColors;
    distributionChart.update();
};
'''

# 2. Hook renderTrainingFilter into initAnalytics
initAnalytics_hook_old = r'''    // 4. Temporal Stability \(Flicker\)
    const ctxStab = document.getElementById\('stability-canvas'\);'''
initAnalytics_hook_new = '''    // UI initializations for Filters
    window.renderTrainingFilter();
    window.renderDistanceFilter();
    
    // 4. Temporal Stability (Flicker)
    const ctxStab = document.getElementById('stability-canvas');'''

content = content.replace(initAnalytics_hook_old, initAnalytics_hook_new)
content = training_js + '\n' + content


# 3. Hook metrics parsing into Training Data Raw update
metrics_parse_old = r'''                confChart.data.datasets\[0\].data = tp;
                confChart.data.datasets\[1\].data = fn;
                confChart.update\(\);
                
                // Update Per-Class Accuracy based on TP / \(TP\+FN\)
                if \(classBarChart\) \{
                    const acc = tp.map\(\(val, i\) => \{
                        const total = val \+ fn\[i\];
                        return total > 0 \? \(val / total\) \* 100 : 0;
                    \}\);
                    classBarChart.data.datasets\[0\].data = acc;
                    classBarChart.update\(\);
                \}

                // Update Data Distribution Chart
                if \(distributionChart\) \{
                    const classTotals = cm.map\(row => row.reduce\(\(sum, val\) => sum \+ val, 0\)\);
                    distributionChart.data.datasets\[0\].data = classTotals;
                    distributionChart.update\(\);
                \}'''
                
metrics_parse_new = '''                const acc = tp.map((val, i) => {
                    const total = val + fn[i];
                    return total > 0 ? (val / total) * 100 : 0;
                });
                const classTotals = cm.map(row => row.reduce((sum, val) => sum + val, 0));
                
                // Update global data container and redraw charts through filter
                // If CM returns fewer/more labels, we rely on the static 7 labels mapped to indexes,
                // or we adapt if metrics.classes exists. For now, assume lengths match up to defaultClasses.
                if (metrics.classes && metrics.classes.length > 0) {
                    window.trainingDataRaw.labels = metrics.classes;
                }
                window.trainingDataRaw.tp = tp;
                window.trainingDataRaw.fn = fn;
                window.trainingDataRaw.acc = acc;
                window.trainingDataRaw.classTotals = classTotals;
                
                // Reset filter state if new labels loaded
                if (metrics.classes) window.trainingFilterState = {};
                
                window.renderTrainingFilter();
                window.updateTrainingCharts();'''

content = re.sub(metrics_parse_old, metrics_parse_new, content, flags=re.MULTILINE)

# 4. State and Helper for Distance Chart Filter
distance_js = '''window.distanceFilterState = {};

window.renderDistanceFilter = function() {
    const container = document.getElementById('distance-filter-dropdown');
    if (!container) return;
    container.innerHTML = '';
    
    // Only road surfaces
    const surfaceLabels = defaultClasses.filter(lbl => window.getCategory(lbl) === 'Surfaces');
    
    surfaceLabels.forEach(lbl => {
        if (window.distanceFilterState[lbl] === undefined) {
            window.distanceFilterState[lbl] = true;
        }
        
        const wrapper = document.createElement('label');
        wrapper.className = 'flex items-center justify-between gap-2 mb-1 p-1 hover:bg-[#222] cursor-pointer rounded';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'w-3 h-3 rounded bg-gray-700 border-gray-600 text-cyan-500 cursor-pointer';
        checkbox.checked = window.distanceFilterState[lbl];
        checkbox.onchange = (e) => {
            window.distanceFilterState[lbl] = e.target.checked;
            window.updateMapState(); // Redraws distance chart
        };
        const text = document.createElement('span');
        text.className = 'text-[10px] uppercase font-mono text-gray-300 whitespace-nowrap';
        text.innerText = lbl;
        wrapper.appendChild(checkbox);
        wrapper.appendChild(text);
        container.appendChild(wrapper);
    });
};'''

dist_chart_update_old = r'''    // Update Distance Bar Chart
    if \(distanceChart\) \{
        const labels = Object.keys\(distanceAgg\);
        const data = labels.map\(l => distanceAgg\[l\].toFixed\(2\)\);
        const colors = labels.map\(l => window.classState\[l\] \? window.classState\[l\].color : '#888'\);
        
        distanceChart.data.labels = labels;
        distanceChart.data.datasets\[0\].data = data;
        distanceChart.data.datasets\[0\].backgroundColor = colors;
        distanceChart.update\(\);
    \}'''

dist_chart_update_new = '''    // Update Distance Bar Chart
    if (distanceChart) {
        // Enforce the distance filter dropdown bounds!
        // We only show items if they are checked in distanceFilterState AND they appeared in distanceAgg
        // OR they are checked in distanceFilterState but have 0 distance.
        const fLabels = [];
        const fData = [];
        const fColors = [];
        
        Object.keys(window.distanceFilterState).forEach(lbl => {
            if (window.distanceFilterState[lbl]) {
                fLabels.push(lbl);
                fData.push(distanceAgg[lbl] ? distanceAgg[lbl].toFixed(2) : "0.00");
                fColors.push(window.classState[lbl] ? window.classState[lbl].color : '#888');
            }
        });
        
        distanceChart.data.labels = fLabels;
        distanceChart.data.datasets[0].data = fData;
        distanceChart.data.datasets[0].backgroundColor = fColors;
        distanceChart.update();
    }'''

content = content.replace(initAnalytics_hook_new, distance_js + '\n' + initAnalytics_hook_new)
content = re.sub(dist_chart_update_old, dist_chart_update_new, content, flags=re.MULTILINE)

with open('desktop-app/src/renderer.js', 'w', encoding='utf-8') as f:
    f.write(content)

