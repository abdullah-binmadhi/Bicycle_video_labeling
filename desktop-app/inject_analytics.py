import re

with open("/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html", "r") as f:
    text = f.read()

nav_str = r"""<li onclick="switchView('view-inference')"><a><svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>Real-Time Inference</a></li>"""

new_nav_str = nav_str + """\n              <!-- Phase 1: Analytics -->\n              <li onclick="switchView('view-analytics')"><a><svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>Model Analytics</a></li>"""

if "view-analytics" not in text:
    if nav_str in text:
        text = text.replace(nav_str, new_nav_str)

    # Insert view-analytics just before closing Scrolling Views Wrapper
    # Use exact same structure as view-inference replacement script above
    analytics_view = """
        <!-- View: Analytics (Feature 4, 8) -->
        <div id="view-analytics" class="hidden-view p-8 space-y-6 flex flex-col gap-6 w-full max-w-5xl mx-auto pb-10">
          <div class="flex justify-between items-center">
            <div>
              <h1 class="text-3xl font-extrabold text-white tracking-tight">Post-Training Analytics</h1>
              <p class="text-sm text-slate-400 mt-2">Confusion matrices, cross-session validations, and precision diagnostics.</p>
            </div>
            <button class="btn btn-outline border-white/20 text-blue-400 hover:bg-blue-500 hover:text-white" onclick="generatePDFReport()">
              <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              Export PDF Report
            </button>
          </div>
          
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="glass-card p-6 rounded-2xl border border-white/5 shadow-xl flex flex-col items-center min-h-[350px]">
               <h3 class="text-emerald-400 font-bold tracking-widest text-xs uppercase self-start mb-4 w-full border-b border-white/10 pb-2">Confusion Matrix (Validation)</h3>
               <canvas id="confusion-canvas" class="w-full h-full"></canvas>
            </div>
            <div class="glass-card p-6 rounded-2xl border border-white/5 shadow-xl flex flex-col items-center min-h-[350px]">
               <h3 class="text-rose-400 font-bold tracking-widest text-xs uppercase self-start mb-4 w-full border-b border-white/10 pb-2">Precision / Recall Radar</h3>
               <canvas id="radar-canvas" class="w-full h-full"></canvas>
            </div>
          </div>
          
          <div class="glass-card p-6 rounded-2xl border border-white/5 shadow-xl w-full">
            <h3 class="text-blue-400 font-bold tracking-widest text-xs uppercase mb-4 w-full border-b border-white/10 pb-2">Session Generalization (Drift)</h3>
            <div class="flex gap-4 mb-4">
                <select class="select select-bordered select-sm flex-1 bg-slate-900 border-white/10 text-slate-300">
                    <option>iOS Run A</option>
                </select>
                <span class="text-slate-500 font-bold my-auto">VS</span>
                <select class="select select-bordered select-sm flex-1 bg-slate-900 border-white/10 text-slate-300">
                    <option>Android Run B</option>
                </select>
                <button class="btn btn-sm btn-primary">Compare Overlap</button>
            </div>
            <div class="w-full h-[250px]">
                <canvas id="drift-canvas" class="w-full h-full"></canvas>
            </div>
          </div>
        </div>
        
"""
    # Insert before the `</div> <!-- End Scrolling Views Wrapper -->`
    wrapper_close_idx = text.rfind("</div> <!-- End Scrolling Views Wrapper -->")
    if wrapper_close_idx != -1:
        text = text[:wrapper_close_idx] + analytics_view + text[wrapper_close_idx:]

    # Also install html2pdf script
    if "html2pdf.js" not in text:
        text = text.replace("<!-- Inject JS libraries -->", "<!-- Inject JS libraries -->\n      <script src=\"https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js\"></script>")

    with open("/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html", "w") as f:
        f.write(text)
    
    print("HTML updated for Analytics.")
else:
    print("Analytics already present.")
