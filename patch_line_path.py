import re

with open('desktop-app/src/renderer.js', 'r') as f:
    content = f.read()

# Regex to safely replace the entire updateMapState function logic related to map rendering
old_func_pattern = re.compile(
    r'    // Arrays for distance calculation.*?// Update Distance Bar Chart',
    re.DOTALL
)

new_func_body = """    // Arrays for distance calculation
    const distanceAgg = {};

    // 1. ALWAYS draw a visible baseline white path so the shape of the route is intact
    const pathCoords = window.currentGeoData.map(pt => [pt.lat, pt.lon]);
    if (pathCoords.length > 0) {
        L.polyline(pathCoords, {
            color: '#ffffff', // More visible white mark
            weight: 3,
            opacity: 0.5,
            smoothFactor: 1
        }).addTo(geoLayerGroup);
    }

    let prevActualPt = null;

    // We process sequentially, connecting visible points along the actual path
    for (const pt of window.currentGeoData) {
        if (!pt.surface) continue;
        let s = pt.surface;
        let isVisible = window.classState[s] && window.classState[s].visible;
        let color = window.classState[s] ? window.classState[s].color : '#fff';
        let dist = parseFloat(pt.distance_m || 0);
        let cat = window.getCategory(s);

        // Aggregate distance ALWAYS so dropdown filter works independently of map visibility
        if (!distanceAgg[s]) distanceAgg[s] = 0;
        distanceAgg[s] += dist;

        if (isVisible) {
            // Draw either Line segment or Dot
            if (drawLinesMode && cat === 'Surfaces') {
                // Connect the literal preceding geographic point to this visible point to follow the mark exactly
                if (prevActualPt) {
                    L.polyline([[prevActualPt.lat, prevActualPt.lon], [pt.lat, pt.lon]], {
                        color: color, // color by current point's surface
                        weight: 5,
                        opacity: 0.9 // Highlight strongly
                    }).bindTooltip(`<b>${s}</b><br/>Dist: ${dist}m`, {
                        className: 'bg-[#111] text-white border-[#333]'
                    }).addTo(geoLayerGroup);
                }
            } else {
                // If NOT a surface, or we are in Dots mode, render as a dot
                L.circleMarker([pt.lat, pt.lon], {
                    radius: 5,
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

        // ALWAYS update the track of the literal previous point on the map path so we never skip over hidden road sections
        prevActualPt = pt;
    }

    // Update Distance Bar Chart"""

if old_func_pattern.search(content):
    content = old_func_pattern.sub(new_func_body, content)
    with open('desktop-app/src/renderer.js', 'w') as f:
        f.write(content)
    print("Patched updateMapState rendering successfully.")
else:
    print("Could not find the updateMapState rendering logic.")
