import re

with open("/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html", "r") as f:
    text = f.read()

# 1. Add Leaflet CSS to head
if "leaflet.css" not in text:
    head_end = text.find("</head>")
    text = text[:head_end] + '  <link rel="stylesheet" href="../node_modules/leaflet/dist/leaflet.css">\n' + text[head_end:]

# 2. Modify Inference View Grid
grid_search = re.search(r'(<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">.*?)(</div>\s*</div>\s*<!-- Global Console Output -->)', text, re.DOTALL)

if grid_search:
    original_grid = grid_search.group(1)
    
    # We will just append the two new panes before the closing tags of the grid
    new_panes = """
            <!-- GPS Heatmap -->
            <div class="glass-card p-4 rounded-2xl border border-white/5 shadow-xl flex flex-col relative min-h-[350px] bg-slate-900/50">
               <h3 class="text-blue-400 font-bold tracking-widest text-[10px] uppercase mb-2 absolute top-4 left-4 z-[400] bg-slate-900/80 px-2 py-1 rounded">Global Position Trace</h3>
               <div id="inf-map" class="w-full h-full rounded z-0 rounded-xl border border-white/10" style="min-height: 300px;"></div>
            </div>

            <!-- 3D Digital Twin -->
            <div class="glass-card p-4 rounded-2xl border border-white/5 shadow-xl flex flex-col relative min-h-[350px] bg-slate-900/50 items-center justify-center">
               <h3 class="text-amber-400 font-bold tracking-widest text-[10px] uppercase mb-2 absolute top-4 left-4 z-10 bg-slate-900/80 px-2 py-1 rounded">3D Orientation Twin</h3>
               <div id="inf-3d-canvas" class="w-full h-full rounded z-0 flex items-center justify-center" style="min-height: 300px;">
                  <p class="text-slate-500 font-medium text-sm">Awaiting IMU stream...</p>
               </div>
            </div>
"""
    
    # Insert new panes before the last closing div of the grid
    modified_grid = original_grid[:original_grid.rfind('</div>')] + new_panes + '          </div>\n'
    
    # Replace in text
    text = text[:grid_search.start()] + modified_grid + grid_search.group(2) + text[grid_search.end():]
    
# 3. Add Leaflet and Three.js scripts
if "leaflet.js" not in text:
    js_inject = """      <script src="../node_modules/leaflet/dist/leaflet.js"></script>
      <script src="../node_modules/three/build/three.min.js"></script>"""
    text = text.replace("<!-- Inject JS libraries -->", f"<!-- Inject JS libraries -->\n{js_inject}")

with open("/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html", "w") as f:
    f.write(text)

print("HTML Structure Updated!")