import re

html_path = 'desktop-app/src/index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

start_marker = '<!-- View: Training -->'
end_marker = '<!-- View: Inference -->'

start_idx = html.find(start_marker)
end_idx = html.find(end_marker)

if start_idx != -1 and end_idx != -1:
    old_block = html[start_idx:end_idx]
    
    new_block = """<!-- View: Training -->
        <div id="view-train" class="hidden-view flex flex-col gap-6 w-full max-w-4xl mx-auto pb-10">
          <div class="flex justify-between items-end mb-2">
            <div class="flex-1">
              <h2 class="text-3xl font-medium text-white tracking-tight">Transformer Training</h2>
              <div class="flex flex-col gap-2 mt-2 w-full">
                  <p class="text-[#888888]">Initialize the PyTorch Engine. Gradients are dynamically tracked.</p>
                  
                  <!-- Checkpoint Select & Resume -->
                  <div class="flex items-center gap-3">
                      <div class="bg-rose-950/20 border border-rose-500/20 p-2 rounded-none flex items-center gap-3 w-max">
                          <button class="btn btn-xs rounded-none border border-rose-500/40 bg-rose-500/10 text-rose-300 hover:bg-rose-500/30" onclick="chooseResumeModel()">Select Checkpoint to Resume</button>
                          <input type="text" placeholder="Start fresh (random weights)..." readonly class="input input-xs bg-transparent border-0 text-rose-200 font-mono text-[10px] w-48 p-0 focus:outline-none" id="trainResumePath" />
                          <button class="btn btn-circle btn-xs btn-ghost text-rose-400 hover:bg-rose-500/20" onclick="document.getElementById('trainResumePath').value=''" title="Clear Checkpoint">
                              <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                          </button>
                      </div>
                      
                      <!-- Force Stop Button (Initially Hidden) -->
                      <button id="btn-train-stop" class="btn btn-sm border border-red-500/50 bg-red-900/20 text-red-400 hover:bg-red-500/40 hover:text-white hidden transition-all duration-300 rounded-none shadow-lg" onclick="stopActiveProcess()">
                          <svg class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" /></svg>
                          Force Stop Early
                      </button>
                  </div>
              </div>
            </div>
            
            <button class="btn border-0 bg-rose-600 hover:bg-rose-500 text-white px-8 h-12 shadow-rose-900/30" onclick="runScript('train')" id="btn-train">
              <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              Burn Neural Weights
              <span class="loading loading-spinner hidden w-4 h-4 ml-2" id="spinner-train"></span>
            </button>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start mt-2">
              <!-- Hyperparameters & Settings -->
              <div class="border border-[#222] bg-[#0c0c0c] p-6 shadow-xl space-y-5">
                  <h3 class="text-white font-medium flex items-center gap-2 border-b border-white/5 pb-3">
                      <svg class="w-4 h-4 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                      Hyperparameters
                  </h3>
                  
                  <div class="grid grid-cols-3 gap-3">
                      <div>
                          <label class="text-[10px] uppercase font-bold text-slate-400 mb-1 block">Epochs</label>
                          <input type="number" id="train-epochs" placeholder="50" min="1" max="1000" class="input input-sm w-full bg-black border-[#333] focus:border-rose-400 text-white font-mono" />
                      </div>
                      <div>
                          <label class="text-[10px] uppercase font-bold text-slate-400 mb-1 block">Learning Rm</label>
                          <input type="number" id="train-lr" placeholder="0.001" step="0.0001" class="input input-sm w-full bg-black border-[#333] focus:border-rose-400 text-white font-mono" />
                      </div>
                      <div>
                          <label class="text-[10px] uppercase font-bold text-slate-400 mb-1 block">Batch Sz</label>
                          <input type="number" id="train-batch" placeholder="32" min="1" class="input input-sm w-full bg-black border-[#333] focus:border-rose-400 text-white font-mono" />
                      </div>
                  </div>

                  <div class="flex flex-col w-full text-left pt-2 border-t border-white/5">
                      <label class="text-[10px] uppercase font-bold text-slate-400 mb-2">Target Training Matrix (CSV)</label>
                      <div class="join w-full shadow-inner">
                        <button class="btn btn-sm join-item bg-slate-700 border-[#333] text-white hover:bg-slate-600" onclick="chooseTrainData()">Choose</button>
                        <input type="text" placeholder="Defaults to config.yaml target..." class="input input-sm join-item w-full bg-slate-950 border-[#333] focus:border-rose-400 text-white font-mono text-[10px]" id="trainDataPath" />
                      </div>
                  </div>
              </div>

              <!-- Modality Switches -->
              <div class="border border-[#222] bg-[#0c0c0c] p-6 shadow-xl space-y-5 h-full">
                  <h3 class="text-white font-medium flex items-center gap-2 border-b border-white/5 pb-3">
                      <svg class="w-4 h-4 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
                      Sensor Architecture
                  </h3>
                  
                  <div class="space-y-3">
                      <!-- Vision -->
                      <div class="bg-black border border-[#333] hover:border-purple-500/30 transition-colors p-2 px-3 rounded-none flex items-center justify-between">
                          <div class="flex items-center gap-3">
                              <div class="w-6 h-6 bg-purple-500/10 text-purple-400 flex items-center justify-center shrink-0 border border-purple-500/20"><svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg></div>
                              <div>
                                  <h4 class="text-white font-medium text-[11px]">Vision Embeddings</h4>
                                  <p class="text-[9px] text-slate-500">Camera-based latent vectors</p>
                              </div>
                          </div>
                          <input type="checkbox" class="toggle toggle-accent toggle-sm" id="toggle-vision" />
                      </div>

                      <!-- IMU -->
                      <div class="bg-black border border-[#333] hover:border-teal-500/30 transition-colors p-2 px-3 rounded-none flex items-center justify-between">
                          <div class="flex items-center gap-3">
                              <div class="w-6 h-6 bg-teal-500/10 text-teal-400 flex items-center justify-center shrink-0 border border-teal-500/20"><svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg></div>
                              <div>
                                  <h4 class="text-white font-medium text-[11px]">IMU Physics Timeline</h4>
                                  <p class="text-[9px] text-slate-500">6-DoF Vibration Sequences</p>
                              </div>
                          </div>
                          <input type="checkbox" class="toggle toggle-info toggle-sm" id="toggle-imu" checked />
                      </div>
                  </div>
              </div>
          </div>

          <!-- Chart.js and Live Data Canvas -->
          <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mt-4 animate-fade-in" id="training-stats" style="display: none;"> <!-- Revealed via JS -->
            <!-- Small Stat Cards -->
            <div class="col-span-1 space-y-4">
              <div class="border border-[#222] bg-[#0c0c0c] rounded-none p-5 border-l-4 border-l-blue-500 shadow-xl">
                <p class="text-[10px] uppercase font-bold text-[#888888] tracking-widest flex items-center gap-2">
                   <span class="relative flex h-2 w-2"><span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75 hidden" id="ping-epoch"></span><span class="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span></span>
                   Epoch
                </p>
                <div class="flex items-baseline mt-2">
                    <p class="text-4xl font-normal tracking-tight text-white font-mono" id="stat-epoch">0</p>
                    <p class="text-xs text-slate-500 font-mono ml-2">/ <span id="stat-epoch-total">?</span></p>
                </div>
              </div>
              <div class="border border-[#222] bg-[#0c0c0c] rounded-none p-5 border-l-4 border-l-rose-500 shadow-xl transition-all duration-300" id="loss-card">
                <p class="text-[10px] uppercase font-bold text-[#888888] tracking-widest flex items-center justify-between">
                   Val Loss (MSE)
                   <span id="loss-trend" class="text-xs"></span>
                </p>
                <p class="text-4xl font-normal tracking-tight text-white mt-2 font-mono" id="stat-loss">0.000</p>
              </div>
            </div>
            
            <!-- Beautiful Canvas Render -->
              <div class="col-span-3 border border-[#222] bg-[#0c0c0c] p-6 rounded-none relative h-[250px] shadow-xl">
                <p class="absolute top-4 left-6 text-[10px] uppercase font-bold text-slate-500 tracking-widest z-10" id="chart-title">Loss Trajectory Map</p>
                <canvas id="lossChart" class="w-full h-full"></canvas>
              </div>
            </div>
          </div> <!-- End view-train -->

          <!-- View: Inference -->"""
    
    html = html.replace(old_block, new_block)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("HTML UI update successful")
else:
    print("Could not find markers in HTML")

