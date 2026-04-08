import re

with open('desktop-app/src/index.html', 'r') as f:
    content = f.read()

# 1. Remove "Charts Row Header & Filter" to the start of "Geospatial Distribution Map"
# But we need to KEEP the "Total Distance per Surface (m)" chart. Actually, let's extract it and put it somewhere.
# Wait, "Advanced Analytics Row" contains both Distribution and Distance.
# Let's use regex to find and remove specific blocks.

# Remove Charts Row Header & Filter
content = re.sub(
    r'<!-- Charts Row Header & Filter -->.*?</div>\s*</div>\s*</div>', 
    '', 
    content, 
    flags=re.DOTALL
)

# Remove Charts Row
content = re.sub(
    r'<!-- Charts Row -->\s*<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">.*?</div>\s*</div>',
    '',
    content,
    flags=re.DOTALL
)

# Keep the distance chart by replacing the Advanced Analytics Row with JUST the distance chart row in a 1-col grid.

distance_chart_html = """
  <!-- Distance Summary -->
  <div class="flex flex-col gap-6 w-full">
      <div class="border border-[#222] bg-[#0c0c0c] p-6 flex flex-col items-center min-h-[300px]">
           <div class="w-full flex justify-between items-center border-b border-[#333] pb-2 mb-4">
               <h3 class="text-cyan-400 font-medium tracking-widest text-xs uppercase self-start">Total Distance per Surface (m)</h3>
               <div class="relative group">
                 <button class="text-xs text-gray-400 hover:text-white flex items-center gap-1"><i class="fa-solid fa-filter"></i> Filter</button>
                 <div class="absolute right-0 top-full mt-2 w-48 bg-[#111] border border-[#333] max-h-48 overflow-y-auto hidden group-hover:flex flex-col z-50 shadow-xl p-2" id="distance-filter-dropdown">
                 </div>
               </div>
           </div>
           <div class="w-full h-full relative h-[250px]">
             <canvas id="distance-canvas" class="w-full h-full"></canvas>
           </div>
        </div>
  </div>
"""

content = re.sub(
    r'<!-- Advanced Analytics Row -->.*?</div>\s*</div>\s*</div>',
    distance_chart_html,
    content,
    flags=re.DOTALL
)

# Remove Hardest Edge Cases / Misclassifications
content = re.sub(
    r'<!-- Hardest Edge Cases / Misclassifications -->.*?</table>\s*</div>\s*</div>',
    '',
    content,
    flags=re.DOTALL
)

with open('desktop-app/src/index.html', 'w') as f:
    f.write(content)
print("Removed charts from HTML.")
