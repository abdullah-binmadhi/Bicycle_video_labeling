with open("desktop-app/src/index.html", "r") as f:
    lines = f.readlines()

out = []
i = 0
while i < len(lines):
    if "<!-- Charts Row Header & Filter -->" in lines[i]:
        # Skip everything until Geospatial Distribution Map
        while i < len(lines) and "<!-- Geospatial Distribution Map -->" not in lines[i]:
            i += 1
            
        # Before inserting Geospatial Map, we add our cleaned distance chart
        distance_chart = """
  <!-- Distance Summary -->
  <div class="flex flex-col gap-6 w-full mb-6">
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
        out.append(distance_chart)
        
        # Now append the Geospatial Dist Map header
        out.append(lines[i])
        i += 1
    elif "<!-- Hardest Edge Cases / Misclassifications -->" in lines[i]:
        # Skip everything until we find the closing div of this container.
        # This div looks like `<div class="border border-[#222] bg-[#0c0c0c] p-6 w-full">` which is at i+1
        # Then inside is `table`...
        # So we can keep skipping until we see the "<!-- Global Console Output -->" minus the closing `</div>` of the "Scrolling Views Wrapper"
        # Or better yet, explicitly skip a set number of lines or match the table ending.
        # Let's count divs explicitly if needed, but it's easier to find "        </tbody>\n      </table>\n    </div>\n  </div>\n"
        while i < len(lines) and '<tbody id="misclassification-tbody">' not in lines[i]:
            i += 1
        # Skip down until table wraps up
        while i < len(lines) and '</table>' not in lines[i]:
            i+=1
        # skip `    </div>`
        i += 1
        # skip `  </div>`
        i += 1
        # Next line should be the end of the Hardest Edge Cases. 
        # i.e. </div>  </div> (but let's just let the main loop continue)
        
    else:
        out.append(lines[i])
        i += 1

with open("desktop-app/src/index.html", "w") as f:
    f.writelines(out)

