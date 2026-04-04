import os

html_path = '/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

start_marker = '<!-- View: Synchronization -->'
end_marker = '<!-- View: Training -->'

start_idx = html.find(start_marker)
end_idx = html.find(end_marker)

if start_idx != -1 and end_idx != -1:
    old_block = html[start_idx:end_idx]
    
    new_block = """<!-- View: Synchronization -->
        <div id="view-sync" class="hidden-view flex flex-col gap-6 w-full max-w-4xl mx-auto pb-10">
          <div>
            <h2 class="text-3xl font-medium text-white tracking-tight">Temporal Alignment</h2>
            <p class="text-[#888888] mt-1">Accurately align time-series data streams from different sensors using exact timestamp matching to generate a unified dataset.</p>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 w-full">
            <!-- Global / Ad-Hoc Sync Settings -->
            <div class="border border-[#222] bg-[#0c0c0c] p-6 flex flex-col items-start gap-4 shadow-xl">
              <h3 class="text-lg font-medium text-white flex items-center justify-between w-full">
                <span class="flex items-center gap-2">
                  <svg class="h-5 w-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" /></svg>
                  Input Parameters
                </span>
                <div class="join">
                   <input type="radio" name="sync-source-type" value="global" class="join-item btn btn-xs input-xs border-[#555] checked:bg-emerald-500 checked:text-white" aria-label="Global" checked onchange="document.getElementById('global-sync-inputs').classList.remove('hidden'); document.getElementById('adhoc-sync-inputs').classList.add('hidden');" />
                   <input type="radio" name="sync-source-type" value="adhoc" class="join-item btn btn-xs input-xs border-[#555] checked:bg-emerald-500 checked:text-white" aria-label="Session" onchange="document.getElementById('adhoc-sync-inputs').classList.remove('hidden'); document.getElementById('global-sync-inputs').classList.add('hidden');" />
                </div>
              </h3>
              
              <div class="w-full">
                <!-- Global Inputs -->
                <div id="global-sync-inputs" class="flex flex-col gap-2 mt-4 animate-fade-in w-full">
                  <label class="text-xs uppercase tracking-widest font-medium text-[#888888] mb-0 block">Database Root</label>
                  <div class="join w-full">
                    <button class="btn btn-sm join-item bg-slate-700 border-[#333] text-white hover:bg-slate-600" onclick="chooseSyncDir()">Choose Folder</button>
                    <input type="text" placeholder="Defaults to BicycleData..." class="input input-sm join-item w-full bg-black border-[#333] text-white font-mono text-[10px]" id="syncDataPath" />
                  </div>
                  <p class="text-[10px] text-slate-500 italic mt-1">Automatically discovers all sessions to merge.</p>
                </div>

                <!-- Ad-Hoc Inputs -->
                <div id="adhoc-sync-inputs" class="hidden flex flex-col gap-3 mt-4 animate-fade-in w-full">
                  <label class="text-xs uppercase tracking-widest font-medium text-[#888888] mb-0 block">Upload Individual Files</label>
                  <div class="join w-full">
                    <button class="btn btn-sm join-item bg-slate-700 border-[#333] text-white hover:bg-slate-600 w-24">IMU CSV</button>
                    <input type="text" placeholder="e.g. Telemetry/IMU.csv" class="input input-sm join-item w-full bg-black border-[#333] text-white font-mono text-[10px]" id="adhocImuPath" />
                  </div>
                  <div class="join w-full">
                    <button class="btn btn-sm join-item bg-slate-700 border-[#333] text-white hover:bg-slate-600 w-24">Label CSV</button>
                    <input type="text" placeholder="e.g. VideoFrames/Label.0.csv" class="input input-sm join-item w-full bg-black border-[#333] text-white font-mono text-[10px]" id="adhocLabelPath" />
                  </div>
                   <p class="text-[10px] text-slate-500 italic mt-1">Bypass global search. Directly merge two isolated tables.</p>
                </div>
              </div>
            </div>

            <!-- Tolerance & Gap Handling -->
            <div class="border border-[#222] bg-[#0c0c0c] p-6 flex flex-col items-start gap-4 shadow-xl">
              <h3 class="text-lg font-medium text-white flex items-center gap-2">
                <svg class="h-5 w-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                Temporal Logic
              </h3>

              <div class="w-full">
                  <div class="flex justify-between text-xs text-slate-400 mb-2">
                    <span class="font-medium text-[10px] uppercase tracking-wide">Merge Tolerance</span>
                    <span id="sync-tolerance-val" class="font-mono text-white text-[10px] bg-slate-800 px-1.5 py-0.5 rounded border border-white/10">50 ms</span>
                  </div>
                  <input type="range" min="10" max="1000" value="50" step="10" class="range range-xs range-info opacity-90" id="sync-tolerance-slider" oninput="document.getElementById('sync-tolerance-val').innerText = this.value + ' ms'" />
                  <p class="text-[9px] text-[#777] mt-1 leading-tight">Maximum allowed clock gap drop-off boundary.</p>
              </div>

              <div class="w-full mt-2">
                 <label class="text-[10px] uppercase tracking-widest font-medium text-slate-400 mb-2 block">Gap Imputation Strategy</label>
                 <select class="select select-sm w-full bg-black border-[#333] focus:border-cyan-400 text-white text-xs" id="sync-gap-handling">
                    <option value="ffill" selected>Forward-Fill (Hold previous ground truth)</option>
                    <option value="interpolate">Linear Interpolation (Mathematical fading)</option>
                    <option value="drop">Strict Drop (Remove unpaired rows)</option>
                 </select>
              </div>
            </div>
          </div>

          <div class="border border-[#222] bg-[#0c0c0c] flex flex-col lg:flex-row items-center justify-between p-6 gap-6 shadow-xl">
            <!-- Actionable DSP Filter Toggle -->
            <div class="bg-black border border-[#333] p-3 rounded-none flex items-center gap-4 text-left w-full lg:w-1/2">
                <div class="w-10 h-10 rounded-none bg-amber-500/20 text-amber-400 flex items-center justify-center shrink-0 border border-amber-500/30">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"/></svg>
                </div>
                <div class="flex-1">
                    <h4 class="text-white font-medium text-xs tracking-wide">Apply Quarter-Car DSP</h4>
                    <p class="text-[9px] text-[#888888] leading-tight">Cut Road Resonance from frame bounce.</p>
                </div>
                <input type="checkbox" class="toggle toggle-warning toggle-sm" id="toggle-dsp" checked />
            </div>

            <button class="btn border-0 bg-white text-slate-900 hover:bg-slate-200 px-12 rounded-none font-bold tracking-wider w-full lg:w-auto self-stretch flex-1" onclick="runScript('sync')" id="btn-sync">
              INITIATE VECTOR MERGE
              <span class="loading loading-spinner hidden w-4 h-4 border-slate-900 ml-2" id="spinner-sync"></span>
            </button>
          </div>

          <!-- Post-Sync Analytics Dashboard (Hidden initially) -->
          <div id="sync-analytics-board" class="hidden grid grid-cols-3 gap-4 border border-emerald-500/20 bg-emerald-950/20 p-5 w-full items-center animate-fade-in shadow-xl">
             <div class="flex flex-col items-center justify-center text-center">
                 <h4 class="text-[10px] text-slate-400 uppercase tracking-widest font-bold">Rows Merged</h4>
                 <span class="text-2xl font-mono text-emerald-400 tracking-tighter mt-1" id="sync-stat-rows">0</span>
             </div>
             <div class="flex flex-col items-center justify-center text-center border-l border-white/5 pl-4">
                 <h4 class="text-[10px] text-slate-400 uppercase tracking-widest font-bold">Orphaned / Dropped</h4>
                 <span class="text-2xl font-mono text-rose-400 tracking-tighter mt-1" id="sync-stat-drops">0%</span>
             </div>
             <div class="flex flex-col items-center justify-center text-center border-l border-white/5 pl-4">
                 <h4 class="text-[10px] text-slate-400 uppercase tracking-widest font-bold">Major Classes Map</h4>
                 <div class="flex flex-wrap gap-1 mt-2 items-center justify-center text-[10px] text-white" id="sync-stat-classes">
                     <!-- dynamically filled, e.g., <span class="badge bg-slate-800 border-emerald-500/30">Asphalt</span> -->
                 </div>
             </div>
          </div>
        </div>

        """
    
    html = html.replace(old_block, new_block)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("UI update successful")
else:
    print("Could not find markers")
