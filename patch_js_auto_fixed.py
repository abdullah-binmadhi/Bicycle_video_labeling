import re

with open("desktop-app/src/renderer.js", "r") as f:
    content = f.read()

# 1. ADD window.classState ONLY ONCE globally
state_init = """window.currentGeoData = [];
window.classState = {};

window.updateMapState = function() {
    if (!geoLayerGroup || !analyticsMap) return;
    analyticsMap.removeLayer(geoLayerGroup);
    geoLayerGroup = L.layerGroup().addTo(analyticsMap);
    
    for (const pt of window.currentGeoData) {
        if (!pt.surface) continue;
        let s = pt.surface;
        if (!window.classState[s] || !window.classState[s].visible) continue;
        
        let color = window.classState[s].color;
        let lat = pt.lat;
        let lon = pt.lon;
        let plusCode = pt.plusCode || 'N/A';
        
        L.circleMarker([lat, lon], {
            radius: 3,
            fillColor: color,
            color: color,
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
        }).bindTooltip(`<b>${s}</b><br/><span class="font-mono text-xs">${plusCode}</span>`, {
            className: 'bg-[#111] text-white border-[#333]'
        }).addTo(geoLayerGroup);
    }
};

window.renderLegend = function() {
    const container = document.getElementById('dynamic-legend-controls');
    if (!container) return;
    
    // UNHIDE THE LEGEND OVERLAY!
    if (container.parentElement) {
        container.parentElement.classList.remove('hidden');
    }
    
    container.innerHTML = '';
    
    for (const className in window.classState) {
        const state = window.classState[className];
        
        const wrapper = document.createElement('div');
        wrapper.className = 'flex items-center gap-2 mb-2';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.checked = state.visible;
        checkbox.className = 'w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-500 focus:ring-offset-gray-800 cursor-pointer';
        checkbox.onchange = (e) => {
            window.classState[className].visible = e.target.checked;
            window.updateMapState();
        };
        
        const colorPicker = document.createElement('input');
        colorPicker.type = 'color';
        colorPicker.value = state.color;
        colorPicker.className = 'w-6 h-6 p-0 border-0 rounded cursor-pointer bg-transparent';
        colorPicker.oninput = (e) => {
            window.classState[className].color = e.target.value;
            window.updateMapState();
        };
        
        const label = document.createElement('span');
        label.className = 'text-xs text-gray-300 font-mono flex-1 capitalize';
        label.innerText = className;
        
        wrapper.appendChild(checkbox);
        wrapper.appendChild(colorPicker);
        wrapper.appendChild(label);
        container.appendChild(wrapper);
    }
};

window.registerSurface = function(surface) {
    if (!surface) return;
    if (!window.classState[surface]) {
        let defColor = '#ccc';
        let sLow = surface.toLowerCase();
        if (sLow.includes('asphalt') || sLow.includes('tarmac') || sLow.includes('134')) defColor = '#10b981';
        else if (sLow.includes('gravel') || sLow.includes('8')) defColor = '#f59e0b';
        else if (sLow.includes('cobble') || sLow.includes('19')) defColor = '#3b82f6';
        else if (sLow.includes('pothole') || sLow.includes('crack') || sLow.includes('1')) defColor = '#ef4444';
        else if (sLow.includes('speed bump') || sLow.includes('speed_bump') || sLow.includes('5')) defColor = '#a855f7';
        else if (sLow.includes('bicycle lane') || sLow.includes('bicycle_lane') || sLow.includes('133')) defColor = '#2dd4bf';
        else if (sLow.includes('rail_tracks') || sLow.includes('rail tracks') || sLow.includes('18')) defColor = '#64748b';
        
        window.classState[surface] = {
            visible: true,
            color: defColor
        };
    }
};"""

# Replace ONLY the first global occurance of window.currentGeoData
content = content.replace("window.currentGeoData = [];\n", state_init + "\n", 1)

# 2. Extract loadGeospatialCSV loop and remove hardcoded colors
geo_csv_pattern = re.compile(r"window\.currentGeoData\.push\(\{lat,\s*lon,\s*surface,\s*plusCode\}\);\s*let\s+color\s*=\s*'#ccc';.*?\.addTo\(geoLayerGroup\);", re.DOTALL)
content = geo_csv_pattern.sub("window.currentGeoData.push({lat, lon, surface, plusCode});\n            window.registerSurface(surface);", content)

# 3. Insert updateMapState and renderLegend safely inside loadGeospatialCSV bounds block
bounds_pattern = re.compile(r"if\s*\(bounds\.length\s*>\s*0\)\s*\{\s*analyticsMap\.fitBounds\(bounds,\s*\{\s*padding:\s*\[20,\s*20\]\s*\}\);\s*document\.getElementById\('geo-stats-text'\)\.innerText\s*=\s*`Loaded\s*\$\{bounds\.length\}\s*waypoints\s*via\s*\+Codes`;\s*\}", re.DOTALL)
bounds_repl = r"""if (bounds.length > 0) {
            analyticsMap.fitBounds(bounds, { padding: [20, 20] });
            document.getElementById('geo-stats-text').innerText = `Loaded ${bounds.length} waypoints via +Codes`;
            window.renderLegend();
            window.updateMapState();
        }"""
content = bounds_pattern.sub(bounds_repl, content)

# 4. Extract processCSV loop and remove hardcoded colors
process_csv_pattern = re.compile(r"window\.currentGeoData\.push\(\{\s*lat:\s*lat,\s*lon:\s*lon,\s*surface:\s*surfaceType,.*?\.addTo\(geoLayerGroup\);\s*totalPoints\+\+;", re.DOTALL)
process_csv_repl = """window.currentGeoData.push({
                    lat: lat,
                    lon: lon,
                    surface: surfaceType, // Match the key used in exporting
                    plusCode: plusCode
                });
                
                window.registerSurface(surfaceType);
                totalPoints++;"""
content = process_csv_pattern.sub(process_csv_repl, content)

# 5. Add updateMapState and renderLegend to scanDirectory end
scan_end_pattern = re.compile(r"if\s*\(window\.currentGeoData\.length\s*>\s*0\)\s*\{\s*// Fit map bounds to the markers\s*const\s+bounds\s*=\s*L\.latLngBounds\(window\.currentGeoData\.map\(d\s*=>\s*\[d\.lat,\s*d\.lon\]\)\);\s*analyticsMap\.fitBounds\(bounds,\s*\{\s*padding:\s*\[50,\s*50\]\s*\}\);\s*\}", re.DOTALL)
scan_end_repl = """if (window.currentGeoData.length > 0) {
        // Fit map bounds to the markers
        const bounds = L.latLngBounds(window.currentGeoData.map(d => [d.lat, d.lon]));
        analyticsMap.fitBounds(bounds, { padding: [50, 50] });
        window.renderLegend();
        window.updateMapState();
    }"""
content = scan_end_pattern.sub(scan_end_repl, content)

with open("desktop-app/src/renderer.js", "w") as f:
    f.write(content)
print("renderer.js successfully patched without duplication.")
