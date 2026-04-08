import re

with open('desktop-app/src/renderer.js', 'r') as f:
    content = f.read()

# Fix the chart initialization by making sure it targets canvas 'distance-canvas'.

chart_logic = """
    // Update Distance Bar Chart
    const barCtx = document.getElementById('distance-canvas'); // FIXED
    if (barCtx) {
        const labels = Object.keys(distanceAgg);
        const data = labels.map(l => distanceAgg[l]);
        const bColors = labels.map(l => (window.classState[l] && window.classState[l].color) ? window.classState[l].color : '#555');

        if (window.distanceChartInstance) {
            window.distanceChartInstance.data.labels = labels;
            window.distanceChartInstance.data.datasets[0].data = data;
            window.distanceChartInstance.data.datasets[0].backgroundColor = bColors;
            window.distanceChartInstance.update();
        } else {
            window.distanceChartInstance = new Chart(barCtx, {
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

content = re.sub(r'\/\/ Update Distance Bar Chart.*?(?=\s*window\.updateCharts|$)', chart_logic, content, flags=re.DOTALL)

with open('desktop-app/src/renderer.js', 'w') as f:
    f.write(content)
