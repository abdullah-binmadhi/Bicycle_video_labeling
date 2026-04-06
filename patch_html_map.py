import re

with open("desktop-app/src/index.html", "r") as f:
    content = f.read()

pattern = re.compile(
    r'(<div class="w-full h-\[400px\] relative bg-\[#111\] z-0 overflow-hidden" id="analytics-map">\s*<!-- Leaflet Map Container -->\s*)</div>\s*<div class="mt-3 flex gap-4 text-\[10px\] sm:text-xs text-slate-400 justify-center flex-wrap">.*?<span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-\[#64748b\]"></span> 18 - rail_tracks</span>\s*</div>',
    re.DOTALL
)

replacement = r"""\1
        <!-- Interactive Map Legend Overlay -->
        <div class="absolute top-4 right-4 bg-[#0c0c0c]/90 backdrop-blur-md border border-[#333] p-4 rounded-lg shadow-2xl z-[1000] w-64 max-h-[90%] overflow-y-auto hidden" id="map-legend-container">
            <h3 class="text-xs uppercase tracking-widest font-bold text-emerald-400 mb-3 border-b border-[#333] pb-2">Surface Filters</h3>
            <div id="dynamic-legend-controls" class="flex flex-col gap-2"></div>
        </div>
    </div>"""

content_new, count = pattern.subn(replacement, content)

if count > 0:
    with open("desktop-app/src/index.html", "w") as f:
        f.write(content_new)
    print("Patched map legend")
else:
    print("Failed to patch")
