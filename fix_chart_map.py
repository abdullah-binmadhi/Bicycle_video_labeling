import re

with open('desktop-app/src/renderer.js', 'r') as f:
    text = f.read()

# 1. Destroy old static `distanceChart` initialization in initAnalytics
# We find: // 5.5 Distance Distribution Bar Chart down to options: { ... } } }); }
chart_init_regex = re.compile(r'// 5\.5 Distance Distribution Bar Chart.*?\}\s*\);\s*\}', re.DOTALL)
text = chart_init_regex.sub('// 5.5 Distance Distribution Bar Chart initialization deferred to updateMapState', text)

# 2. Fix the loop in updateMapState to connect previous points to new segments in line mode
# and remove `cat === 'Surfaces'` restriction so lines act continuously.
loop_regex = re.compile(r'    let currentSegmentPoints = \[\];.*?commitSegment\(\); // Commit remaining points', re.DOTALL)

improved_loop = """    let currentSegmentPoints = [];
    let currentSegmentSurface = null;
    let currentSegmentDistance = 0;
    let prevPtCoords = null;

    // Helper to draw accumulated segment
    function commitSegment() {
        if (currentSegmentPoints.length > 1 && currentSegmentSurface) {
            let isVisible = window.classState[currentSegmentSurface] && window.classState[currentSegmentSurface].visible;
            if (isVisible) {
                let color = window.classState[currentSegmentSurface].color || '#fff';
                let distKm = (currentSegmentDistance / 1000).toFixed(4); // Convert meters to KM
                L.polyline(currentSegmentPoints, {
                    color: color,
                    weight: 6,
                    opacity: 0.9 
                }).bindTooltip(`<b>${currentSegmentSurface}</b><br/>Segment length: ${distKm} KM`, {
                    className: 'bg-[#111] text-white border-[#333]'
                }).addTo(geoLayerGroup);
            }
        } else if (currentSegmentPoints.length === 1 && currentSegmentSurface && !drawLinesMode) {
             let isVisible = window.classState[currentSegmentSurface] && window.classState[currentSegmentSurface].visible;
             if (isVisible) {
                 let color = window.classState[currentSegmentSurface].color || '#fff';
                 L.circleMarker(currentSegmentPoints[0], {
                    radius: 5,
                    fillColor: color,
                    color: color,
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.8
                }).bindTooltip(`<b>${currentSegmentSurface}</b>`, {
                    className: 'bg-[#111] text-white border-[#333]'
                }).addTo(geoLayerGroup);
             }
        }
        currentSegmentPoints = [];
        currentSegmentDistance = 0;
        currentSegmentSurface = null;
    }

    for (const pt of window.currentGeoData) {
        if (!pt.surface) continue;
        let s = pt.surface;
        let dist = parseFloat(pt.distance_m || 0);

        if (!distanceAgg[s]) distanceAgg[s] = 0;
        distanceAgg[s] += dist;

        let isVisible = window.classState[s] && window.classState[s].visible;

        if (drawLinesMode) {
            if (s === currentSegmentSurface) {
                currentSegmentPoints.push([pt.lat, pt.lon]);
                currentSegmentDistance += dist;
            } else {
                commitSegment();
                currentSegmentSurface = s;
                // Connect back to the ending point of the previous segment to prevent gaps
                currentSegmentPoints = prevPtCoords ? [prevPtCoords, [pt.lat, pt.lon]] : [[pt.lat, pt.lon]];
                currentSegmentDistance = dist;
            }
        } else {
             commitSegment();
             if (isVisible) {
                 let color = window.classState[s] ? window.classState[s].color : '#fff';
                 L.circleMarker([pt.lat, pt.lon], {
                    radius: 5,
                    fillColor: color,
                    color: color,
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.8
                 }).bindTooltip(`<b>${s}</b><br/>Dist: ${dist}m`, {
                    className: 'bg-[#111] text-white border-[#333]'
                 }).addTo(geoLayerGroup);
             }
        }
        prevPtCoords = [pt.lat, pt.lon];
    }
    commitSegment(); // Commit remaining points"""

text = loop_regex.sub(improved_loop, text)

# Ensure chart doesn't try to use Chart property globally improperly.
# Need to make sure distance-canvas exists and is properly created.
chart_update_regex = re.compile(r'// Update Distance Bar Chart\s*const barCtx = document\.getElementById\(\'distance-canvas\'\);.*?\}\s*\}', re.DOTALL)

chart_update_replacement = """// Update Distance Bar Chart
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
    }"""

text = chart_update_regex.sub(chart_update_replacement, text)

with open('desktop-app/src/renderer.js', 'w') as f:
    f.write(text)
    
