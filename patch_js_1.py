import re

with open('desktop-app/src/renderer.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add global variable
content = content.replace("let distributionChart = null;", "let distributionChart = null;\nlet distanceChart = null;")

# 2. Add chart init inside initAnalytics()
old_chart_init = r'''    // 5\. Data Distribution
    const ctxDist = document\.getElementById\('distribution-canvas'\);
    if\(ctxDist && !distributionChart\) \{
        distributionChart = new Chart\(ctxDist, \{
            type: 'doughnut',
            data: \{
                labels: \['134 - asphalt', '8 - gravel', '19 - cobblestone', '1 - potholes', '5 - speed_bump', '133 - bicycle_lane', '18 - rail_tracks'\],
                datasets: \[\{
                    data: \[1500, 800, 450, 200, 100, 150, 300\],
                    backgroundColor: \['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#a855f7', '#2dd4bf', '#64748b'\],
                    borderWidth: 0
                \}\]
            \},
            options: \{ responsive: true, maintainAspectRatio: false \}
        \}\);
    \}'''

new_chart_init = '''    // 5. Data Distribution
    const ctxDist = document.getElementById('distribution-canvas');
    if(ctxDist && !distributionChart) {
        distributionChart = new Chart(ctxDist, {
            type: 'doughnut',
            data: {
                labels: ['134 - asphalt', '8 - gravel', '19 - cobblestone', '1 - potholes', '5 - speed_bump', '133 - bicycle_lane', '18 - rail_tracks'],
                datasets: [{
                    data: [1500, 800, 450, 200, 100, 150, 300],
                    backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#a855f7', '#2dd4bf', '#64748b'],
                    borderWidth: 0
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

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
    }'''

content = re.sub(old_chart_init, new_chart_init, content, flags=re.MULTILINE)

with open('desktop-app/src/renderer.js', 'w', encoding='utf-8') as f:
    f.write(content)

