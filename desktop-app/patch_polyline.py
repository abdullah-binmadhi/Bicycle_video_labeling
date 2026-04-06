import re

with open("src/renderer.js", "r") as f:
    content = f.read()

old_str = """window.updateMapState = function() {
    if (!geoLayerGroup || !analyticsMap) return;
    analyticsMap.removeLayer(geoLayerGroup);
    geoLayerGroup = L.layerGroup().addTo(analyticsMap);
    
    for (const pt of window.currentGeoData) {"""

new_str = """window.updateMapState = function() {
    if (!geoLayerGroup || !analyticsMap) return;
    analyticsMap.removeLayer(geoLayerGroup);
    geoLayerGroup = L.layerGroup().addTo(analyticsMap);
    
    // Draw the unified route path first
    const pathCoords = window.currentGeoData.map(pt => [pt.lat, pt.lon]);
    if (pathCoords.length > 0) {
        L.polyline(pathCoords, {
            color: '#666666',
            weight: 2,
            opacity: 0.5,
            smoothFactor: 1
        }).addTo(geoLayerGroup);
    }
    
    for (const pt of window.currentGeoData) {"""

if old_str in content:
    with open("src/renderer.js", "w") as f:
        f.write(content.replace(old_str, new_str))
    print("Patched successfully")
else:
    print("Failed to find string")

