import re

with open('desktop-app/src/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the 3-column row with two 2-column rows
old_charts_row = r'''  <!-- Advanced Analytics Row -->
  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 w-full">
    <div class="border border-\[#222\] bg-\[#0c0c0c\] p-6 flex flex-col items-center min-h-\[300px\]">
       <h3 class="text-emerald-400 font-medium tracking-widest text-xs uppercase self-start mb-4 w-full border-b border-\[#333\] pb-2">Loss Convergence Curve</h3>
       <div class="w-full h-full relative relative h-\[250px\]">
         <canvas id="convergence-canvas" class="w-full h-full"></canvas>
       </div>
    </div>
    <div class="border border-\[#222\] bg-\[#0c0c0c\] p-6 flex flex-col items-center min-h-\[300px\]">
       <h3 class="text-amber-400 font-medium tracking-widest text-xs uppercase self-start mb-4 w-full border-b border-\[#333\] pb-2">Temporal Stability \(Flicker\)</h3>
       <div class="w-full h-full relative relative h-\[250px\]">
         <canvas id="stability-canvas" class="w-full h-full"></canvas>
       </div>
    </div>
    <div class="border border-\[#222\] bg-\[#0c0c0c\] p-6 flex flex-col items-center min-h-\[300px\]">
       <h3 class="text-fuchsia-400 font-medium tracking-widest text-xs uppercase self-start mb-4 w-full border-b border-\[#333\] pb-2">Data Distribution</h3>
       <div class="w-full h-full relative relative h-\[250px\]">
         <canvas id="distribution-canvas" class="w-full h-full"></canvas>
       </div>
    </div>
  </div>'''

new_charts_row = '''  <!-- Advanced Analytics Row -->
  <div class="flex flex-col gap-6 w-full">
      <!-- Top Row 2x1 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
        <div class="border border-[#222] bg-[#0c0c0c] p-6 flex flex-col items-center min-h-[300px]">
           <h3 class="text-emerald-400 font-medium tracking-widest text-xs uppercase self-start mb-4 w-full border-b border-[#333] pb-2">Loss Convergence Curve</h3>
           <div class="w-full h-full relative h-[250px]">
             <canvas id="convergence-canvas" class="w-full h-full"></canvas>
           </div>
        </div>
        <div class="border border-[#222] bg-[#0c0c0c] p-6 flex flex-col items-center min-h-[300px]">
           <h3 class="text-amber-400 font-medium tracking-widest text-xs uppercase self-start mb-4 w-full border-b border-[#333] pb-2">Temporal Stability (Flicker)</h3>
           <div class="w-full h-full relative h-[250px]">
             <canvas id="stability-canvas" class="w-full h-full"></canvas>
           </div>
        </div>
      </div>
      <!-- Bottom Row 2x1 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
        <div class="border border-[#222] bg-[#0c0c0c] p-6 flex flex-col items-center min-h-[300px]">
           <h3 class="text-fuchsia-400 font-medium tracking-widest text-xs uppercase self-start mb-4 w-full border-b border-[#333] pb-2">Data Distribution</h3>
           <div class="w-full h-full relative h-[250px]">
             <canvas id="distribution-canvas" class="w-full h-full"></canvas>
           </div>
        </div>
        <div class="border border-[#222] bg-[#0c0c0c] p-6 flex flex-col items-center min-h-[300px]">
           <h3 class="text-cyan-400 font-medium tracking-widest text-xs uppercase self-start mb-4 w-full border-b border-[#333] pb-2">Total Distance per Surface (m)</h3>
           <div class="w-full h-full relative h-[250px]">
             <canvas id="distance-canvas" class="w-full h-full"></canvas>
           </div>
        </div>
      </div>
  </div>'''

content = re.sub(old_charts_row, new_charts_row, content, flags=re.MULTILINE)

# Also add the toggle switch in the Map Filters
old_map_header = r'''                <h3 class="text-xs uppercase tracking-widest font-bold text-emerald-400">Filters</h3>
                <div class="flex gap-2">
                    <button onclick="for\(const k in window.classState\) window.classState\[k\].visible=true; window.renderLegend\(\); window.updateMapState\(\);" class="text-\[10px\] uppercase font-mono text-cyan-500 hover:text-cyan-300">All</button>
                    <button onclick="for\(const k in window.classState\) window.classState\[k\].visible=false; window.renderLegend\(\); window.updateMapState\(\);" class="text-\[10px\] uppercase font-mono text-rose-500 hover:text-rose-300">None</button>
                </div>
            </div>'''
            
new_map_header = '''                <h3 class="text-xs uppercase tracking-widest font-bold text-emerald-400">Filters</h3>
                <div class="flex gap-2">
                    <button onclick="for(const k in window.classState) window.classState[k].visible=true; window.renderLegend(); window.updateMapState();" class="text-[10px] uppercase font-mono text-cyan-500 hover:text-cyan-300">All</button>
                    <button onclick="for(const k in window.classState) window.classState[k].visible=false; window.renderLegend(); window.updateMapState();" class="text-[10px] uppercase font-mono text-rose-500 hover:text-rose-300">None</button>
                </div>
            </div>
            
            <div class="mb-4 pb-3 border-b border-[#333]">
                <label class="flex items-center cursor-pointer">
                  <div class="relative">
                    <input type="checkbox" id="map-render-toggle" class="sr-only" onchange="window.updateMapState()">
                    <div class="block bg-gray-600 w-10 h-6 rounded-full"></div>
                    <div class="dot absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition select-none pointer-events-none"></div>
                  </div>
                  <div class="ml-3 text-gray-300 text-xs uppercase font-mono tracking-wider" id="map-render-label">
                    Mode: Dots
                  </div>
                </label>
            </div>
            <style>
              input:checked ~ .dot {
                transform: translateX(100%);
                background-color: #10b981;
              }
            </style>
'''

content = re.sub(old_map_header, new_map_header, content, flags=re.MULTILINE)

with open('desktop-app/src/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

