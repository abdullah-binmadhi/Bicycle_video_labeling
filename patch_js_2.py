import re

with open('desktop-app/src/renderer.js', 'r', encoding='utf-8') as f:
    content = f.read()

old_map_state = r'''        window.currentGeoData = \[\];
window.classState = \{\};

window.updateMapState = function\(\) \{
    if \(!geoLayerGroup \|\| !analyticsMap\) return;
    analyticsMap.removeLayer\(geoLayerGroup\);
    geoLayerGroup = L.layerGroup\(\).addTo\(analyticsMap\);
    
    // Draw the unified route path first
    const pathCoords = window.currentGeoData.map\(pt => \[pt.lat, pt.lon\]\);
    if \(pathCoords.length > 0\) \{
        L.polyline\(pathCoords, \{
            color: '#666666',
            weight: 2,
            opacity: 0.5,
            smoothFactor: 1
        \}\).addTo\(geoLayerGroup\);
    \}
    
    for \(const pt of window.currentGeoData\) \{
        if \(!pt.surface\) continue;
        let s = pt.surface;
        if \(!window.classState\[s\] \|\| !window.classState\[s\].visible\) continue;
        
        let color = window.classState\[s\].color;
        let lat = pt.lat;
        let lon = pt.lon;
        let plusCode = pt.plusCode \|\| 'N/A';
        
        L.circleMarker\(\[lat, lon\], \{
            radius: 3,
            fillColor: color,
            color: color,
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
        \}\).bindTooltip\(`<b>\$\{s\}</b><br/><span class="font-mono text-xs">\$\{plusCode\}</span>`, \{
            className: 'bg-\[#111\] text-white border-\[#333\]'
        \}\).addTo\(geoLayerGroup\);
    \}
\};'''

new_map_state = '''        // Generate proper mocked map data with distances
        window.currentGeoData = [];
        let curr_lat = base_lat;
        let curr_lon = base_lon;
        for (let i = 0; i < 100; i++) {
            curr_lat += (Math.random() - 0.5) * 0.002;
            curr_lon += (Math.random() - 0.5) * 0.002 + 0.001; // drift east
            let s = surfaces[Math.floor(Math.random() * surfaces.length)];
            window.currentGeoData.push({
                lat: curr_lat,
                lon: curr_lon,
                surface: s,
                plusCode: '9F4M' + Math.floor(Math.random()*8999+1000),
                distance_m: (Math.random() * 5 + 1).toFixed(2)
            });
        }
        
window.classState = {};

window.updateMapState = function() {
    if (!geoLayerGroup || !analyticsMap) return;
    analyticsMap.removeLayer(geoLayerGroup);
    geoLayerGroup = L.layerGroup().addTo(analyticsMap);
    
    let drawLinesMode = false;
    const toggle = document.getElementById('map-render-toggle');
    if (toggle) drawLinesMode = toggle.checked;

    const lbl = document.getElementById('map-render-label');
    if (lbl) lbl.innerText = drawLinesMode ? 'Mode: Lines' : 'Mode: Dots';
    
    // Arrays for distance calculation
    const distanceAgg = {};

    let prevPt = null;
    let prevColor = null;
    let prevVisible = false;

    // We process sequentially, connecting visible points
    for (const pt of window.currentGeoData) {
        if (!pt.surface) continue;
        let s = pt.surface;
        let isVisible = window.classState[s] && window.classState[s].visible;
        let color = window.classState[s] ? window.classState[s].color : '#fff';
        let dist = parseFloat(pt.distance_m || 0);

        if (isVisible) {
            // Aggregate distance
            if (!distanceAgg[s]) distanceAgg[s] = 0;
            distanceAgg[s] += dist;

            // Draw either Line segment or Dot
            if (drawLinesMode) {
                if (prevVisible && prevPt) {
                    L.polyline([[prevPt.lat, prevPt.lon], [pt.lat, pt.lon]], {
                        color: color, // color by current point's surface
                        weight: 4,
                        opacity: 0.8
                    }).bindTooltip(`<b>${s}</b><br/>Dist: ${dist}m`, {
                        className: 'bg-[#111] text-white border-[#333]'
                    }).addTo(geoLayerGroup);
                }
            } else {
                L.circleMarker([pt.lat, pt.lon], {
                    radius: 4,
                    fillColor: color,
                    color: color,
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.8
                }).bindTooltip(`<b>${s}</b><br/><span class="font-mono text-xs">${pt.plusCode || 'N/A'}</span><br/>Dist: ${dist}m`, {
                    className: 'bg-[#111] text-white border-[#333]'
                }).addTo(geoLayerGroup);
            }
        }

        prevPt = pt;
        prevVisible = isVisible;
        prevColor = color;
    }
    
    // Fallback: draw unified gray path underneath if in dots mode
    if (!drawLinesMode) {
        const pathCoords = window.currentGeoData.map(pt => [pt.lat, pt.lon]);
        if (pathCoords.length > 0) {
            L.polyline(pathCoords, {
                color: '#666666',
                weight: 2,
                opacity: 0.3,
                smoothFactor: 1
            }).addTo(geoLayerGroup);
        }
    }

    // Update Distance Bar Chart
    if (window.distanceChart) {
        const labels = Object.keys(distanceAgg);
        const data = labels.map(l => distanceAgg[l].toFixed(2));
        const colors = labels.map(l => window.classState[l] ? window.classState[l].color : '#888');
        
        window.distanceChart.data.labels = labels;
        window.distanceChart.data.datasets[0].data = data;
        window.distanceChart.data.datasets[0].backgroundColor = colors;
        window.distanceChart.update();
    }
};'''

content = re.sub(old_map_state, new_map_state, content, flags=re.MULTILINE)

with open('desktop-app/src/renderer.js', 'w', encoding='utf-8') as f:
    f.write(content)

