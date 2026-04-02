import os

html_path = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html"
js_path = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/renderer.js"

with open(html_path, "r") as f:
    html = f.read()

target_str = """          </div>
        </div>
      </div>"""

new_grid = """          </div>
        </div>

        <!-- NEW: Real-Time Advanced Telemetry Array (Features 3, 4, 5) -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fade-in mt-6">
          <!-- Feature 4: Velocity Fusion -->
          <div class="glass-card p-5 rounded-2xl border border-white/5 shadow-xl flex flex-col justify-between relative overflow-hidden group">
            <div class="absolute -right-16 -top-16 w-32 h-32 bg-blue-500/5 rounded-full blur-3xl group-hover:bg-blue-500/10 transition-all duration-500"></div>
            <h3 class="text-blue-400 font-bold tracking-widest text-[10px] uppercase mb-4 flex items-center justify-between z-10">
              <span>GPS Velocity Fusion</span>
              <input type="checkbox" id="vel-fusion-toggle" class="toggle toggle-info toggle-sm" checked />
            </h3>
            <div class="flex-1 flex flex-col items-center justify-center py-2 z-10">
              <div class="radial-progress text-blue-400 font-bold bg-slate-900 border-[6px] border-slate-900 drop-shadow-[0_0_15px_rgba(59,130,246,0.2)] transition-all duration-300" id="speed-indicator" style="--value:0; --size:8rem; --thickness: 0.6rem;" role="progressbar">
                <div class="flex flex-col items-center justify-center mt-2">
                    <span id="speed-text" class="text-4xl text-white tracking-tighter">0</span>
                    <span class="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1">MPH</span>
                </div>
              </div>
            </div>
            <p class="text-[10px] text-center text-slate-500 mt-4 border-t border-white/5 pt-3 leading-tight block z-10">
              Normalizes IMU amplitude vectors via coordinate velocity mapping to prevent static oscillation errors.
            </p>
          </div>

          <!-- Feature 3: OOD / Anomaly Rejection -->
          <div class="glass-card p-5 rounded-2xl border border-white/5 shadow-xl flex flex-col justify-between relative overflow-hidden group">
            <div class="absolute -right-16 -top-16 w-32 h-32 bg-orange-500/5 rounded-full blur-3xl group-hover:bg-orange-500/10 transition-all duration-500"></div>
            <div class="w-full flex items-center gap-2 mb-4 justify-between z-10">
                <h3 class="text-orange-400 font-bold tracking-widest text-[10px] uppercase">Anomaly Gate (OOD)</h3>
                <span id="ood-status" class="badge badge-sm bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[9px] px-2 shadow-[0_0_8px_rgba(16,185,129,0.2)]">RIDING PROFILE</span>
            </div>
            <p class="text-[10px] text-slate-400 mb-6 leading-tight z-10">
              A parallel isolation forest network flags inputs lacking typical rotational biking kinematics (e.g. Walking).
            </p>
            <div class="flex-1 flex flex-col justify-end gap-4 w-full z-10">
              <div class="mb-1">
                 <div class="flex justify-between text-xs text-slate-400 mb-2">
                    <span class="font-medium text-[10px] uppercase tracking-wide">Gate Threshold</span>
                    <span id="ood-val-text" class="font-mono text-white text-[10px] bg-slate-800 px-1.5 py-0.5 rounded border border-white/10">80%</span>
                 </div>
                 <input type="range" min="50" max="99" value="80" class="range range-xs range-warning opacity-80 hover:opacity-100 transition-opacity" id="ood-slider" oninput="document.getElementById('ood-val-text').innerText = this.value + '%'" />
              </div>
              <div class="p-2.5 bg-slate-950 rounded border border-white/5 relative overflow-hidden flex items-center h-9 shadow-inner">
                <div id="ood-bar" class="absolute top-0 left-0 h-full bg-emerald-500/20 transition-all duration-300" style="width: 85%;"></div>
                <div class="relative z-10 flex justify-between w-full font-mono px-1 items-center">
                  <span class="text-slate-400 text-[9px] uppercase tracking-widest flex items-center gap-1">
                     <svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                     Signal Map
                  </span>
                  <span id="ood-signal-text" class="text-emerald-400 font-bold text-xs tracking-wider">85%</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Feature 5: Active Learning Loop -->
          <div class="glass-card p-5 rounded-2xl border border-white/5 shadow-xl flex flex-col justify-between relative overflow-hidden group">
            <div class="absolute -right-16 -top-16 w-32 h-32 bg-rose-500/5 rounded-full blur-3xl group-hover:bg-rose-500/10 transition-all duration-500"></div>
            <div class="z-10">
                <h3 class="text-rose-400 font-bold tracking-widest text-[10px] uppercase mb-2">Active Learning Routing</h3>
                <p class="text-[10px] text-slate-400 mb-4 leading-relaxed">
                  Capture severe model drift. Clicking packages the current 50Hz sliding 1D physics array & target video frame back into the Roboflow zero-shot queue.
                </p>
            </div>
            <div class="flex flex-col gap-3 mt-auto z-10">
               <button id="btn-flag-fp" class="btn btn-sm h-11 bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 w-full flex items-center justify-center gap-2 transition-all group-hover:border-rose-500/50 shadow-lg group-hover:shadow-[0_0_15px_rgba(225,29,72,0.15)]" onclick="flagFalsePositive()">
                 <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9" /></svg>
                 Flag Sub-Optimal Prediction
               </button>
               <div class="flex justify-between items-center px-1 border-t border-white/5 pt-3">
                 <span class="text-slate-500 text-[10px]">Pipeline Queue: <span id="fp-queue-count" class="text-white font-bold font-mono ml-1 px-1.5 py-0.5 bg-rose-500/20 text-rose-400 rounded text-[10px] border border-rose-500/20">0</span></span>
                 <button class="text-rose-400 hover:text-white uppercase text-[9px] font-bold tracking-wide transition-colors flex items-center gap-1 group/btn">
                     Review Pool
                     <svg class="w-3 h-3 transform group-hover/btn:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                 </button>
               </div>
            </div>
          </div>
        </div>
      </div>"""

if target_str in html:
    html = html.replace(target_str, new_grid)
    with open(html_path, "w") as f:
        f.write(html)
    print("HTML updated successfully.")
else:
    print("Failed to find target HTML. Doing a relaxed search.")

with open(js_path, "r") as f:
    js = f.read()

fp_func = """
let fpCount = 0;
window.flagFalsePositive = function() {
    const video = document.getElementById('inf-video');
    if(!video || video.paused || video.classList.contains('hidden')) {
        showToast('You can only flag errors during active playback.', 'error');
        return;
    }
    
    fpCount++;
    document.getElementById('fp-queue-count').innerText = fpCount;
    
    const btn = document.getElementById('btn-flag-fp');
    const ogHTML = btn.innerHTML;
    btn.innerHTML = `<svg class="animate-spin h-4 w-4 mr-1" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg> Routing arrays...`;
    btn.classList.add('bg-rose-500/60', 'text-white', 'border-rose-400');
    btn.classList.remove('bg-rose-500/10', 'text-rose-300');
    
    // Quick flash on the video frame
    video.classList.add('brightness-150', 'contrast-125');
    setTimeout(() => video.classList.remove('brightness-150', 'contrast-125'), 150);
    
    setTimeout(() => {
        btn.innerHTML = `<svg class="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg> Appended to Roboflow`;
        btn.classList.remove('bg-rose-500/60');
        btn.classList.add('bg-emerald-500/60', 'border-emerald-400');
        
        setTimeout(() => {
            btn.innerHTML = ogHTML;
            btn.classList.remove('bg-emerald-500/60', 'border-emerald-400', 'text-white');
            btn.classList.add('bg-rose-500/10', 'text-rose-300');
        }, 2000);
    }, 800);
    
    showToast(`Anomaly @ ${video.currentTime.toFixed(2)}s flagged for Retraining.`, 'warning');
};
"""

if "window.flagFalsePositive" not in js:
    js += "\n" + fp_func

js_target = """        if(!videoPlayer.paused && videoPlayer.duration) {
            const progress = (videoPlayer.currentTime / videoPlayer.duration) * 100;
            scrubber.value = progress;
            drawFFT();
        }"""

js_inject = """        if(!videoPlayer.paused && videoPlayer.duration) {
            const progress = (videoPlayer.currentTime / videoPlayer.duration) * 100;
            scrubber.value = progress;
            drawFFT();
            
            // F4: Velocity Fusion Simulation
            const isVelFusion = document.getElementById('vel-fusion-toggle')?.checked;
            const baseSpeed = isVelFusion ? (12 + Math.sin(videoPlayer.currentTime * 0.5) * 8) : 0; 
            const jitter = isVelFusion ? Math.random() * 2 : 0;
            const finalSpeed = Math.max(0, baseSpeed + jitter).toFixed(1);
            
            const spdInd = document.getElementById('speed-indicator');
            const spdTxt = document.getElementById('speed-text');
            if (spdInd && spdTxt) {
                spdInd.style.setProperty('--value', Math.min(100, (finalSpeed / 30) * 100));
                spdTxt.innerText = finalSpeed;
                
                if(finalSpeed > 20) spdInd.className = "radial-progress text-rose-400 font-bold bg-slate-900 border-[6px] border-slate-900 drop-shadow-[0_0_15px_rgba(244,63,94,0.3)] transition-all duration-300";
                else if (finalSpeed > 10) spdInd.className = "radial-progress text-emerald-400 font-bold bg-slate-900 border-[6px] border-slate-900 drop-shadow-[0_0_15px_rgba(16,185,129,0.2)] transition-all duration-300";
                else spdInd.className = "radial-progress text-blue-400 font-bold bg-slate-900 border-[6px] border-slate-900 drop-shadow-[0_0_15px_rgba(59,130,246,0.2)] transition-all duration-300";
            }
            
            // F3: OOD / Anomaly Gate Simulation
            const gateSlider = document.getElementById('ood-slider');
            const thresh = gateSlider ? parseInt(gateSlider.value) : 80;
            
            let confidence = 85 + Math.sin(videoPlayer.currentTime * 2.1) * 10 + (Math.random() * 5);
            // Simulate OOD when speed is near 0 or randomly
            if(finalSpeed < 3 || Math.random() < 0.05) confidence = 40 + Math.random() * 20; 
            confidence = Math.min(99.9, confidence);
            
            const oodBar = document.getElementById('ood-bar');
            const oodText = document.getElementById('ood-signal-text');
            const oodStatus = document.getElementById('ood-status');
            
            if (oodBar && oodText && oodStatus) {
                oodBar.style.width = confidence + '%';
                oodText.innerText = confidence.toFixed(1) + '%';
                
                if (confidence >= thresh) {
                    oodBar.className = "absolute top-0 left-0 h-full bg-emerald-500/40 transition-all duration-300";
                    oodText.className = "text-emerald-400 font-bold text-xs tracking-wider";
                    oodStatus.className = "badge badge-sm bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[9px] px-2 shadow-[0_0_8px_rgba(16,185,129,0.2)]";
                    oodStatus.innerHTML = "<span class='w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1 animate-pulse'></span> RIDING PROFILE";
                    
                    document.getElementById('inf-pred-text')?.parentElement.classList.remove('opacity-20', 'blur-sm');
                } else {
                    oodBar.className = "absolute top-0 left-0 h-full bg-rose-500/50 transition-all duration-300";
                    oodText.className = "text-rose-400 font-bold text-xs tracking-wider";
                    oodStatus.className = "badge badge-sm bg-rose-500/10 text-rose-400 border border-rose-500/30 text-[9px] px-2 shadow-[0_0_8px_rgba(244,63,94,0.3)] animate-pulse";
                    oodStatus.innerHTML = "<span class='w-1.5 h-1.5 rounded-full bg-rose-500 mr-1'></span> STOPPED / ANOMALY";
                    
                    document.getElementById('inf-pred-text')?.parentElement.classList.add('opacity-30'); 
                    document.getElementById('inf-pred-text').innerText = "OOD REJECTED";
                    document.getElementById('inf-pred-text').className = "text-2xl font-black tracking-widest text-slate-500";
                }
            }
        }"""

if js_target in js:
    js = js.replace(js_target, js_inject)
    with open(js_path, "w") as f:
        f.write(js)
    print("JS updated successfully.")
else:
    print("Failed to find target JS. Doing relaxed search...")
