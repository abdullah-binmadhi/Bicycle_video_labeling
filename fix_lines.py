import re

with open('desktop-app/src/renderer.js', 'r') as f:
    content = f.read()

# When drawing a polyline connecting identical surfaces, the user wants the tooltip to show total segment length or distance between them.
# The user stated: "when i toggle line mode, when there are two dots who are the same surface type, they should form a line and when i hover over that line, it tells me the distance between these two lines. even it they are multiple dots who are the same surface, connect them then i can see the distance in KM."

# First, rewrite `updateMapState` to group consecutive points of the SAME surface type into Polylines, calculate the aggregated distance for that segment, and bind a tooltip to the whole line showing the accumulated distance in km.

new_logic = """
window.updateMapState = function() {
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

    // Helper to draw accumulated segment
    function commitSegment() {
        if (currentSegmentPoints.length > 1 && currentSegmentSurface) {
            let isVisible = window.classState[currentSegmentSurface] && window.classState[currentSegmentSurface].visible;
            if (isVisible) {
                let color = window.classState[currentSegmentSurface].color;
                let distKm = (currentSegmentDistance / 1000).toFixed(4); // Convert meters to KM
                L.polyline(currentSegmentPoints, {
                    color: color,
                    weight: 5,
                    opacity: 0.9 
                }).bindTooltip(`<b>${currentSegmentSurface}</b><br/>Segment length: ${distKm} KM`, {
                    className: 'bg-[#111] text-white border-[#333]'
                }).addTo(geoLayerGroup);
            }
        } else if (currentSegmentPoints.length === 1 && currentSegmentSurface && !drawLinesMode) {
             // Fallback for single isolated point if not in strictly line mode or if it happens to be just 1 dot
             let isVisible = window.classState[currentSegmentSurface] && window.classState[currentSegmentSurface].visible;
             if (isVisible) {
                 let color = window.classState[currentSegmentSurface].color;
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
        let cat = window.getCategory(s);

        if (!distanceAgg[s]) distanceAgg[s] = 0;
        distanceAgg[s] += dist;

        let isVisible = window.classState[s] && window.classState[s].visible;

        if (drawLinesMode && cat === 'Surfaces') {
            if (s === currentSegmentSurface) {
                currentSegmentPoints.push([pt.lat, pt.lon]);
                currentSegmentDistance += dist;
            } else {
                commitSegment();
                currentSegmentSurface = s;
                currentSegmentPoints = [[pt.lat, pt.lon]];
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
    }
    commitSegment(); // Commit remaining points

    // Update Distance Bar Chart
"""

pattern = re.compile(r'window\.updateMapState = function\(\) \{.*?\/\/ Update Distance Bar Chart', re.DOTALL)
content = pattern.sub(new_logic, content)

with open('desktop-app/src/renderer.js', 'w') as f:
    f.write(content)
