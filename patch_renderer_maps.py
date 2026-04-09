import sys
import os

with open("desktop-app/src/renderer.js", "a") as f:
    f.write("""

// Added back missing Map rendering logic
window.registerSurface = function(surfaceName) {
    if (!window.classState) window.classState = {};
    if (!window.classState[surfaceName]) {
        const colors = ['#f43f5e', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#a855f7', '#ec4899', '#06b6d4'];
        const numKeys = Object.keys(window.classState).length;
        window.classState[surfaceName] = {
            active: true,
            color: colors[numKeys % colors.length]
        };
    }
};

window.renderLegend = function() {
    const container = document.getElementById('map-legend-container');
    const controls = document.getElementById('dynamic-legend-controls');
    if (!container || !controls) return;
    
    container.classList.remove('hidden');
    container.classList.add('flex');
    controls.innerHTML = '';
    
    for (const surface in window.classState) {
        const state = window.classState[surface];
        let count = (window.currentGeoData || []).filter(d => d.surface === surface).length;
        
        const el = document.createElement('div');
        el.className = 'flex items-center justify-between group p-1 hover:bg-[#222] rounded cursor-pointer transition-colors';
        el.innerHTML = `
            <div class="flex items-center gap-2" onclick="window.toggleSurface('${surface}')">
                <input type="checkbox" ${state.active ? 'checked' : ''} class="checkbox checkbox-sm checkbox-primary rounded-sm border-gray-600 bg-[#111]" />
                <span class="text-sm text-gray-300 font-medium tracking-wide group-hover:text-white transition-colors" style="border-left: 3px solid ${state.color}; padding-left: 6px;">${surface}</span>
            </div>
            <span class="text-xs text-gray-500 font-mono">${count}</span>
        `;
        controls.appendChild(el);
    }
};

window.toggleSurface = function(surface) {
    if (window.classState[surface]) {
        window.classState[surface].active = !window.classState[surface].active;
        window.renderLegend();
        window.updateMapState();
    }
};

window.updateMapState = function() {
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
};
""")
print("Patched renderer maps log.")
