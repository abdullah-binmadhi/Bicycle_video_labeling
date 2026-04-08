import re

with open('desktop-app/src/renderer.js', 'r') as f:
    text = f.read()

# We need to fix the trailing comma and the leftover option bracket block at the end of updateMapState
# Let's cleanly replace the duplicate chart definition or messy regex replace.

# Delete everything from `// Update Distance Bar Chart` to `window.updateCharts` or end of updateMapState
# We will just find `// Update Distance Bar Chart` and precisely replace the rest of the function block.
start_idx = text.find('    // Update Distance Bar Chart')
end_idx = text.find('window.updateCharts', start_idx)

if end_idx == -1:
   # if updateCharts doesn't exist just replace until end of file before DOMContentLoaded or whatever.
   # actually let's just find the `window.distanceChart.update();` loop and close it.
   pass
   
# Let's use regex to replace `// Update Distance Bar Chart` down to the next function definition or EOF.
# Actually, I'll extract it until `});` and then just append exactly the remaining `    }\n}\n`.

clean_code = """// Update Distance Bar Chart
    const barCtx = document.getElementById('distance-canvas'); // FIXED
    if (barCtx) {
        const labels = Object.keys(distanceAgg);
        const data = labels.map(l => distanceAgg[l]);
        const bColors = labels.map(l => (window.classState[l] && window.classState[l].color) ? window.classState[l].color : '#555');

        if (window.distanceChart) {
            window.distanceChart.data.labels = labels;
            window.distanceChart.data.datasets[0].data = data;
            window.distanceChart.data.datasets[0].backgroundColor = bColors;
            window.distanceChart.update();
        } else if (typeof Chart !== 'undefined') {
            window.distanceChart = new Chart(barCtx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Distance (m)',
                        data: data,
                        backgroundColor: bColors,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: 'rgba(255,255,255,0.7)' } },
                        x: { grid: { display: false }, ticks: { color: 'rgba(255,255,255,0.7)', maxRotation: 45, minRotation: 45 } }
                    }
                }
            });
        }
    }
}
"""

clean_regex = re.compile(r'// Update Distance Bar Chart.*', re.DOTALL)
text = clean_regex.sub(clean_code, text)

with open('desktop-app/src/renderer.js', 'w') as f:
    f.write(text)

