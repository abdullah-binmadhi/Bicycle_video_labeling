import re

with open('desktop-app/src/renderer.js', 'r') as f:
    text = f.read()

# Let's just find the whole updateMapState and replace the end of it cleanly.
start_idx = text.find('window.updateMapState = function() {')
end_idx = text.find('window.updateCharts', start_idx)

if start_idx != -1 and end_idx != -1:
    snippet = text[start_idx:end_idx]
    # print("SNIPPET:", snippet)
    
    # We will cleanly put the end of `updateMapState` logic
    # Find `commitSegment(); // Commit remaining points`
    cs_idx = snippet.find('commitSegment(); // Commit remaining points')
    
    if cs_idx != -1:
        new_end = """commitSegment(); // Commit remaining points
    
    // Update Distance Bar Chart
    const barCtx = document.getElementById('distance-canvas');
    if (barCtx) {
        const labels = Object.keys(distanceAgg);
        const data = labels.map(l => distanceAgg[l]);
        const bColors = labels.map(l => (window.classState[l] && window.classState[l].color) ? window.classState[l].color : '#555');

        if (window.distanceChart) {
            window.distanceChart.data.labels = labels;
            window.distanceChart.data.datasets[0].data = data;
            window.distanceChart.data.datasets[0].backgroundColor = bColors;
            window.distanceChart.update();
        } else {
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
                        y: { beginAtZero: true, grid: { color: '#333' } },
                        x: { grid: { display: false } }
                    }
                }
            });
        }
    }
}
"""
        new_snippet = snippet[:cs_idx] + new_end
        
        text = text[:start_idx] + new_snippet + text[end_idx:]
        
        with open('desktop-app/src/renderer.js', 'w') as f:
            f.write(text)
            
