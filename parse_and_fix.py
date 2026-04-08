import re

with open('desktop-app/src/renderer.js', 'r') as f:
    text = f.read()

# 1. Remove ONLY the mock data loop at lines 1348-1369
mock_regex = re.compile(r'\s*for \(let i = 0; i < 50; i\+\+\) \{.*?\.addTo\(geoLayerGroup\);\s*\}', re.DOTALL)
text = mock_regex.sub('\n        // No mock data generated here. Waiting for CSV/Scraper load.', text)

# 2. Replace ONLY `window.updateMapState = function() { ... };` precisely.
raw_func = """window.updateMapState = function() {
    if (!geoLayerGroup || !analyticsMap) return;
    analyticsMap.removeLayer(geoLayerGroup);
    geoLayerGroup = L.layerGroup().addTo(analyticsMap);
    
    let drawLinesMode = false;
    const toggle = document.getElementById('map-render-toggle');
    if (toggle) drawLinesMode = toggle.checked;

    const lbl = document.getElementById('map-render-label');
    if (lbl) lbl.innerText = drawLinesMode ? 'Mode: Lines' : 'Mode: Dots';
    
    const distanceAgg = {};

    // 1. ALWAYS draw a visible baseline white path so the shape of the route is intact
    const pathCoords = window.currentGeoData.map(pt => [pt.lat, pt.lon]);
    if (pathCoords.length > 0) {
        L.polyline(pathCoords, {
            color: '#ffffff', // More visible white mark
            weight: 3,
            opacity: 0.2,
            smoothFactor: 1
        }).addTo(geoLayerGroup);
    }

    let currentSegmentPoints = [];
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
                    radius: 3,
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
    commitSegment(); // Commit remaining points

    // Update Distance Bar Chart
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
};"""

# Find `window.updateMapState = function() { ... };` block exactly
start_idx = text.find('window.updateMapState = function() {')
end_idx = text.find('window.renderLegend = function() {', start_idx)

if start_idx != -1 and end_idx != -1:
    # replace block cleanly
    text = text[:start_idx] + raw_func + '\n\n' + text[end_idx:]

with open('desktop-app/src/renderer.js', 'w') as f:
    f.write(text)

