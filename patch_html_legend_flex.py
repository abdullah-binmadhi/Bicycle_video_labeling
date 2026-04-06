import re

with open("desktop-app/src/index.html", "r") as f:
    content = f.read()

pattern = re.compile(
    r'<div class="w-full h-\[400px\] relative bg-\[#111\] z-0 overflow-hidden" id="analytics-map">\s*<!-- Leaflet Map Container -->\s*<!-- Interactive Map Legend Overlay -->\s*<div class="absolute top-4 right-4 bg-\[#0c0c0c\]/90 backdrop-blur-md border border-\[#333\] p-4 rounded-lg shadow-2xl z-\[1000\] w-64 max-h-\[90%\] overflow-y-auto hidden" id="map-legend-container">\s*<h3 class="text-xs uppercase tracking-widest font-bold text-emerald-400 mb-3 border-b border-\[#333\] pb-2">Surface Filters</h3>\s*<div id="dynamic-legend-controls" class="flex flex-col gap-2"></div>\s*</div>\s*</div>',
    re.DOTALL
)

replacement = r"""<div class="flex flex-col md:flex-row gap-4 w-full h-[400px]">
        <div class="flex-1 relative bg-[#111] z-0 overflow-hidden border border-[#333]" id="analytics-map">
            <!-- Leaflet Map Container -->
        </div>

        <!-- External Interactive Map Legend -->
        <div class="w-full md:w-64 bg-[#0c0c0c] border border-[#333] p-4 overflow-y-auto hidden flex-col shadow-inner" id="map-legend-container">
            <div class="flex justify-between items-center mb-3 border-b border-[#333] pb-2">
                <h3 class="text-xs uppercase tracking-widest font-bold text-emerald-400">Surface Filters</h3>
                <div class="flex gap-2">
                    <button onclick="for(const k in window.classState) window.classState[k].visible=true; window.renderLegend(); window.updateMapState();" class="text-[10px] uppercase font-mono text-cyan-500 hover:text-cyan-300">All</button>
                    <button onclick="for(const k in window.classState) window.classState[k].visible=false; window.renderLegend(); window.updateMapState();" class="text-[10px] uppercase font-mono text-rose-500 hover:text-rose-300">None</button>
                </div>
            </div>
            <div id="dynamic-legend-controls" class="flex flex-col gap-2 overflow-y-auto pr-1"></div>
        </div>
    </div>"""

content_new, count = pattern.subn(replacement, content)

if count > 0:
    with open("desktop-app/src/index.html", "w") as f:
        f.write(content_new)
    print(f"Patched map layout, replaced {count} occurrences")
else:
    print("Failed to match map layout in index.html")
