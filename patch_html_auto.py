import re

html_path = 'desktop-app/src/index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

start_marker = '<!-- View: Data & Annotation -->'
end_marker = '<!-- View: Manual Annotation -->'

start_idx = html.find(start_marker)
end_idx = html.find(end_marker)

if start_idx != -1 and end_idx != -1:
    old_block = html[start_idx:end_idx]
    
    new_block = """<!-- View: Data & Annotation -->
        <div id="view-data" class="hidden-view flex flex-col gap-6 w-full max-w-4xl mx-auto pb-10">
          <div>
            <h2 class="text-3xl font-medium text-white tracking-tight">Two-Stage Auto Annotation (YOLO-World + CLIP)</h2>
            <p class="text-[#888888] mt-1">Leverage a fully automated 2-stage pipeline. YOLO isolates objects, CLIP tags semantic features.</p>
          </div>

          <div class="border border-[#222] bg-[#0c0c0c] p-8 relative overflow-hidden shadow-xl">
            <h3 class="text-lg font-medium text-white mb-6 flex items-center gap-2">
                <svg class="w-5 h-5 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>
                Pipeline Configuration
            </h3>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
              <!-- Directory Settings -->
              <div class="flex flex-col md:col-span-2">
                <label class="text-xs uppercase tracking-widest font-medium text-[#888888] mb-2">1. Input Image Folder (Extracted Frames)</label>
                <div class="join w-full shadow-inner">
                    <button class="btn btn-sm h-10 join-item bg-slate-700 border-[#333] text-white hover:bg-slate-600" onclick="chooseAnnoDir()">Choose Folder</button>
                    <input type="text" placeholder="Select image folder..." class="input input-sm h-10 join-item w-full bg-black border-[#333] focus:border-indigo-400 text-white font-mono text-sm" id="annoDirPath" onchange="setDirectory()" />
                  </div>
                <div class="mt-2 text-[10px] font-mono text-[#e0e0e0]/80 truncate bg-emerald-400/10 p-1.5 rounded hidden" id="selectedDirLabel"></div>
              </div>

              <!-- Output Configuration -->
              <div class="flex flex-col md:col-span-2">
                <label class="text-xs uppercase tracking-widest font-medium text-[#888888] mb-2">2. CSV Output & Checkpoints Folder</label>
                <div class="join w-full shadow-inner">
                  <button class="btn btn-sm h-10 join-item bg-slate-700 border-[#333] text-white hover:bg-slate-600" onclick="chooseClipOutDir()">Choose Output</button>
                  <input type="text" placeholder="Defaults to dataset source folder if blank..." class="input input-sm h-10 join-item w-full bg-black border-[#333] focus:border-indigo-400 text-white font-mono text-sm" id="clipCustomOutPath" />
                </div>
              </div>
            </div>

            <!-- Model Selection & Classes -->
            <div class="mt-8 border-t border-[#222] pt-6">
              <h3 class="text-sm font-semibold mb-4 text-white flex items-center justify-between">
                <span>3. YOLO Target Vocabulary</span>
                <div class="flex items-center gap-2">
                  <input type="checkbox" id="btn-select-all" class="checkbox checkbox-xs checkbox-primary" />
                  <label for="btn-select-all" class="text-[10px] uppercase text-slate-400 cursor-pointer tracking-widest">Select All</label>
                </div>
              </h3>
              
              <div id="clip-classes-container" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 max-h-48 overflow-y-auto mb-6 p-4 bg-[#050505] rounded-none border border-[#333] shadow-inner">
                <!-- Checkboxes dynamically inserted by renderer.js -->
              </div>
            </div>

            <!-- Two-Stage Toggle & Execution -->
            <div class="mt-6 flex items-center justify-between bg-indigo-950/20 border border-indigo-500/20 p-4">
               <div>
                  <h4 class="text-sm font-medium text-white mb-1">Pass YOLO Crops to CLIP (Stage 2)</h4>
                  <p class="text-[10px] text-indigo-200/60 max-w-sm">Automatically pipes the bounding boxes localized by YOLO into the CLIP foundation model to attach dense semantic text tagging.</p>
               </div>
               <input type="checkbox" class="toggle toggle-primary toggle-sm" id="toggle-two-stage" checked />
            </div>

            <!-- Execution Buttons -->
            <div class="mt-6 flex gap-4">
              <button class="btn border-0 bg-indigo-600 hover:bg-indigo-500 text-white px-8 h-12 shadow-indigo-900/30 flex-1 rounded-none" onclick="runScript('clip')" id="btn-clip">
                <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
                Initialize Hybrid Annotation
                <span class="loading loading-spinner hidden w-4 h-4 ml-2" id="spinner-clip"></span>
              </button>
              
              <button id="btn-clip-stop" class="btn h-12 border border-red-500/50 bg-red-950/40 text-red-500 hover:bg-red-500/40 hover:text-white hidden transition-colors rounded-none" onclick="stopClipProcess()">
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" /></svg>
              </button>
            </div>

            <!-- Live Status Board -->
            <div id="auto-anno-stats" class="mt-8 border-t border-[#222] pt-6 hidden">
                <div class="grid grid-cols-3 gap-4">
                   <div class="bg-black border border-[#333] p-4 text-center">
                      <p class="text-[10px] uppercase font-bold text-[#888] tracking-widest">Frames Processed</p>
                      <p class="text-2xl font-mono text-white mt-1" id="stat-anno-frames">0</p>
                   </div>
                   <div class="bg-black border border-[#333] p-4 text-center">
                      <p class="text-[10px] uppercase font-bold text-[#888] tracking-widest">Objects Detected</p>
                      <p class="text-2xl font-mono text-indigo-400 mt-1" id="stat-anno-objects">0</p>
                   </div>
                   <div class="bg-black border border-[#333] p-4 text-center">
                      <p class="text-[10px] uppercase font-bold text-[#888] tracking-widest">Time Remaining</p>
                      <p class="text-2xl font-mono text-emerald-400 mt-1" id="stat-anno-eta">--:--</p>
                   </div>
                </div>
            </div>

          </div>
        </div>

        <!-- View: Manual Annotation -->"""
    
    html = html.replace(old_block, new_block)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("HTML UI update successful")
else:
    print("Could not find markers in HTML")

