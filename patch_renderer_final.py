import sys
import re

path = 'desktop-app/src/renderer.js'
with open(path, 'r') as f:
    text = f.read()

# 1. Default unticked
isolated_old = '''window.registerSurface = function(surfaceName) {
    if (!window.classState) window.classState = {};
    if (!window.classState[surfaceName]) {
        const colors = ['#f43f5e', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#a855f7', '#ec4899', '#06b6d4'];
        const numKeys = Object.keys(window.classState).length;
        window.classState[surfaceName] = {
            active: true,
            color: colors[numKeys % colors.length]
        };
    }
};'''
isolated_new = isolated_old.replace('active: true,', 'active: false,')
text = text.replace(isolated_old, isolated_new)

# 2. Fix Unknown vocabularies
text = text.replace("let surfaceType = classIdx !== -1 && cols[classIdx] ? cols[classIdx] : 'Unknown';", "let surfaceType = classIdx !== -1 && cols[classIdx] ? cols[classIdx].trim() : 'Unclassified'; if (!surfaceType || surfaceType==='Unknown') surfaceType = 'Unclassified';")
text = text.replace("let surface = classIdx !== -1 && row[classIdx] ? row[classIdx].trim() : 'Unknown';", "let surface = classIdx !== -1 && row[classIdx] ? row[classIdx].trim() : 'Unclassified'; if (!surface || surface==='Unknown') surface = 'Unclassified';")
text = text.replace("let surface = classIdx !== -1 ? row[classIdx].trim() : 'Unknown';", "let surface = classIdx !== -1 && row[classIdx] ? row[classIdx].trim() : 'Unclassified'; if (!surface || surface==='Unknown') surface = 'Unclassified';")

old_header_1 = "let classIdx = headers.findIndex(h => h.includes('class') || h.includes('surface') || h.includes('type') || h.includes('label'));"
new_header_1 = "let classIdx = headers.findIndex(h => h.includes('class') || h.includes('surface') || h.includes('type') || h.includes('label') || h.includes('pred') || h.includes('vocab'));"
text = text.replace(old_header_1, new_header_1)

# 3. Add Distance Chart and Haversine
old_updateMapState = '''window.updateMapState = function() {
    if (!geoLayerGroup || !analyticsMap) return;
    analyticsMap.removeLayer(geoLayerGroup);
    geoLayerGroup = L.featureGroup().addTo(analyticsMap);
    
    const pathCoords = (window.currentGeoData || []).map(pt => [pt.lat, pt.lon]);
    if (pathCoords.length > 0) {
        L.polyline(pathCoords, {
            color: '#666666',
            weight: 2,
            opacity: 0.5,
            smoothFactor: 1
        }).addTo(geoLayerGroup);
    }
    
    const activeData = (window.currentGeoData || []).filter(pt => window.classState[pt.surface] && window.classState[pt.surface].active);
    
    for (const pt of activeData) {
        const state = window.classState[pt.surface];
        if (!state) continue;
        L.circleMarker([pt.lat, pt.lon], {
            radius: 4,
            fillColor: state.color,
            color: '#000',
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
        }).bindPopup(`<b>${pt.surface}</b><br>Code: ${pt.plusCode || 'N/A'}`).addTo(geoLayerGroup);
    }
};'''

new_updateMapState = '''
let distanceChartInstance = null;

function getDistance(lat1, lon1, lat2, lon2) {
    const Math_PI = Math.PI;
    const R = 6371e3; // metres
    const phi1 = lat1 * Math_PI/180;
    const phi2 = lat2 * Math_PI/180;
    const dphi = (lat2-lat1) * Math_PI/180;
    const dlambda = (lon2-lon1) * Math_PI/180;
    const a = Math.sin(dphi/2) * Math.sin(dphi/2) +
            Math.cos(phi1) * Math.cos(phi2) *
            Math.sin(dlambda/2) * Math.sin(dlambda/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

window.updateDistanceChart = function() {
    const ctx = document.getElementById('distance-canvas');
    if (!ctx) return;
    
    const distData = {};
    for (let surface in window.classState) {
        distData[surface] = 0;
    }
    
    const geo = window.currentGeoData || [];
    for (let i = 1; i < geo.length; i++) {
        const pt1 = geo[i-1];
        const pt2 = geo[i];
        if (pt1.surface === pt2.surface) {
            distData[pt1.surface] += getDistance(pt1.lat, pt1.lon, pt2.lat, pt2.lon);
        }
    }
    
    const activeSurfaces = Object.keys(window.classState).filter(s => window.classState[s].active);
    const labels = activeSurfaces;
    const data = labels.map(s => Math.round(distData[s]));
    const bgColors = labels.map(s => window.classState[s].color);
    
    if (distanceChartInstance) {
        distanceChartInstance.destroy();
    }
    
    if (typeof Chart === 'undefined') return;
    distanceChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: bgColors,
                borderWidth: 0,
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { color: '#222' }, ticks: { color: '#888' }, title: { display: true, text: 'Distance (m)', color: '#888'} },
                y: { grid: { display: false }, ticks: { color: '#888' } }
            },
            animation: { duration: 300 }
        }
    });
};

window.updateMapState = function() {
    if (!geoLayerGroup || !analyticsMap) return;
    analyticsMap.removeLayer(geoLayerGroup);
    geoLayerGroup = L.featureGroup().addTo(analyticsMap);
    
    const toggleEl = document.getElementById('map-render-toggle');
    const isLineMode = toggleEl ? toggleEl.checked : false;
    const labelEl = document.getElementById('map-render-label');
    if (labelEl) labelEl.innerText = isLineMode ? 'Mode: Line' : 'Mode: Dots';
    
    const geo = window.currentGeoData || [];
    
    if (isLineMode) {
        let currentSegment = [];
        let currentSurface = null;
        
        for (let i = 0; i < geo.length; i++) {
            const pt = geo[i];
            const state = window.classState[pt.surface];
            
            if (!state || !state.active) {
                if (currentSegment.length > 1) {
                    L.polyline(currentSegment.map(p => [p.lat, p.lon]), {
                        color: window.classState[currentSurface].color,
                        weight: 4,
                        opacity: 0.8,
                        smoothFactor: 1
                    }).bindPopup(`<b>${currentSurface}</b>`).addTo(geoLayerGroup);
                }
                currentSegment = [];
                currentSurface = null;
                continue;
            }
            
            if (currentSurface !== pt.surface) {
                if (currentSegment.length > 1) {
                    L.polyline(currentSegment.map(p => [p.lat, p.lon]), {
                        color: window.classState[currentSurface].color,
                        weight: 4,
                        opacity: 0.8,
                        smoothFactor: 1
                    }).bindPopup(`<b>${currentSurface}</b>`).addTo(geoLayerGroup);
                }
                currentSegment = [pt];
                currentSurface = pt.surface;
            } else {
                currentSegment.push(pt);
            }
        }
        
        if (currentSegment.length > 1 && currentSurface) {
            L.polyline(currentSegment.map(p => [p.lat, p.lon]), {
                color: window.classState[currentSurface].color,
                weight: 4,
                opacity: 0.8,
                smoothFactor: 1
            }).bindPopup(`<b>${currentSurface}</b>`).addTo(geoLayerGroup);
        }
        
    } else {
        const pathCoords = geo.map(pt => [pt.lat, pt.lon]);
        if (pathCoords.length > 0) {
            L.polyline(pathCoords, {
                color: '#666666',
                weight: 2,
                opacity: 0.5,
                smoothFactor: 1
            }).addTo(geoLayerGroup);
        }
        
        const activeData = geo.filter(pt => window.classState[pt.surface] && window.classState[pt.surface].active);
        for (const pt of activeData) {
            const state = window.classState[pt.surface];
            if (!state) continue;
            L.circleMarker([pt.lat, pt.lon], {
                radius: 4,
                fillColor: state.color,
                color: '#000',
                weight: 1,
                opacity: 1,
                fillOpacity: 0.8
            }).bindPopup(`<b>${pt.surface}</b><br>Code: ${pt.plusCode || 'N/A'}`).addTo(geoLayerGroup);
        }
    }
    
    if (window.updateDistanceChart) window.updateDistanceChart();
};
'''

text = text.replace(old_updateMapState, new_updateMapState)

with open(path, 'w') as f:
    f.write(text)

print("Renderer.js patched successfully.")
