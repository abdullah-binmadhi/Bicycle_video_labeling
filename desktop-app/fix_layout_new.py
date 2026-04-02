import re

with open("/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html", "r") as f:
    text = f.read()

# find exact block we want to rewrite
start_patt = r"<!-- Beautiful Canvas Render -->.*?</main>\s*</div>"

# First, extract view-inference and global console output
view_inf_patt = r"(<!-- View: Inference -->.*?)<!-- Global Console Output -->"
view_match = re.search(view_inf_patt, text, re.DOTALL)
view_inf_str = view_match.group(1).strip() if view_match else ""

# The global console structure should be:
new_glob_str = r"""<!-- Global Console Output -->
          <div class="w-full flex-shrink-0 z-20 border-t border-white/10 bg-slate-950/80 backdrop-blur-3xl shadow-[0_-20px_40px_-15px_rgba(0,0,0,0.7)]">
            <div class="w-full max-w-5xl mx-auto">
            <div class="glass-card rounded-xl border border-white/10 overflow-hidden shadow-[0_-10px_40px_-15px_rgba(0,0,0,0.5)] bg-slate-950/80 backdrop-blur-3xl">
              <div class="flex items-center justify-between px-4 py-3 border-b border-white/5 bg-black/20 cursor-pointer hover:bg-white/5 transition-colors" onclick="toggleConsole()">
                <div class="text-xs font-bold uppercase tracking-widest text-slate-400 flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l3 3-3 3m5 0h3M4 15V9a2 2 0 012-2h12a2 2 0 012 2v6a2 2 0 01-2 2H6a2 2 0 01-2-2z" /></svg>
                  System Kernel Output
                </div>
                <svg id="console-chevron" class="w-4 h-4 text-slate-500 transform transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" /></svg>
              </div>
              
              <!-- Start Open inside wrapper -->
              <div id="console-wrapper" class="transition-all duration-300 h-[220px]">
                <div id="console-output" class="p-4 h-full overflow-y-auto whitespace-pre-wrap font-mono text-[13px] leading-relaxed text-slate-300"><span class="text-emerald-400 font-bold">$ Engine Matrix Loaded. Welcome to CycleSafe Studio.</span><br/></div>
              </div>
            </div>
            </div>
          </div>"""

match = re.search(start_patt, text, re.DOTALL)
if match:
    beautiful_canvas_str = """<!-- Beautiful Canvas Render -->
              <div class="col-span-3 glass-card rounded-2xl p-5 border border-white/10 relative h-[250px]">
                <p class="absolute top-4 left-6 text-xs uppercase font-bold text-slate-400 tracking-widest z-10 hidden" id="chart-title">Loss Trajectory</p>
                <canvas id="lossChart" class="w-full h-full"></canvas>
              </div>
            </div>
          </div> <!-- End view-train -->"""
    
    new_tail = beautiful_canvas_str + "\n\n          " + view_inf_str + "\n\n        </div> <!-- End Scrolling Views Wrapper -->\n\n" + new_glob_str + "\n\n        </main>\n      </div> <!-- End Content & Layout -->"
    
    new_text = text[:match.start()] + new_tail + text[match.end():]
    
    with open("/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html", "w") as f:
        f.write(new_text)
    print("SUCCESS")
else:
    print("FAILED TO MATCH")