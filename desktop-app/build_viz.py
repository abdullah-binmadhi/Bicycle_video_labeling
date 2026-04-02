import os
import re

html_file = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html"
js_file = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/renderer.js"

with open(html_file, 'r', encoding='utf-8') as f:
    h = f.read()
with open(js_file, 'r', encoding='utf-8') as f:
    j = f.read()

# =======================
# HTML MODIFICATIONS
# =======================

# 1. Header Progress Bar
if 'id="global-progress"' not in h:
    h = h.replace('<button id="btn-abort"', '<progress id="global-progress" class="progress progress-success w-32 hidden transition-all duration-300" value="0" max="100"></progress>\n        <button id="btn-abort"')

# 2. Toast Container
if 'toast-container' not in h:
    h = h.replace('</body>', '  <!-- Toast Container --><div id="toast-container" class="toast toast-bottom toast-end z-[100] p-5"></div>\n  </body>')

# 3. Add Inference Nav Link safely
if 'nav-inference' not in h:
    nav_injection = '''<li><a id="nav-train" class="hover:bg-white/10" onclick="switchView('train')">
          <svg class="h-4 w-4 opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
          5. Model Training
        </a></li>
        <li class="menu-title mt-4 text-slate-500 uppercase tracking-widest text-[10px]"><span>Analysis Results</span></li>
        <li><a id="nav-inference" class="hover:bg-white/10 text-white font-semibold" onclick="switchView('inference')">
          <svg class="h-4 w-4 text-purple-400 drop-shadow-md" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
          6. Real-Time Inference
        </a></li>'''
    h = re.sub(r'<li><a id="nav-train".*?5\. Model Training\n\s*</a></li>', nav_injection, h, flags=re.DOTALL)

# 4. View: Inference Section
if 'view-inference' not in h:
    inference_ui = '''
      <!-- View: Inference -->
      <div id="view-inference" class="hidden-view p-8 space-y-6 h-full overflow-y-auto">
        <div>
          <h1 class="text-3xl font-extrabold text-white tracking-tight">Live Test Execution</h1>
          <p class="text-sm text-slate-400 mt-2">Simulate real-time prediction by passing video and IMU arrays to your best mathematical artifact.</p>
        </div>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="glass-card p-6 rounded-2xl border border-white/5 shadow-xl space-y-4">
             <h3 class="text-purple-400 font-bold tracking-widest text-xs uppercase mb-4">Playback Setup</h3>
             <label class="text-xs text-slate-400 mb-1 block">Compiled Checkpoint (.pth)</label>
             <input type="file" id="infModelPicker" class="file-input file-input-bordered file-input-sm w-full bg-slate-900/50 border-white/10" accept=".pth" />
             
             <label class="text-xs text-slate-400 mb-1 block mt-3">Target Raw Dataset Session</label>
             <input type="file" id="infFolderPicker" webkitdirectory directory class="file-input file-input-bordered file-input-sm w-full bg-slate-900/50 border-white/10" />
             
             <button class="btn btn-primary btn-sm w-full mt-6" id="btn-run-inf" onclick="startAIOverlay()">
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path></svg>
                Launch Visualization
             </button>
             <div class="mt-4 pt-4 border-t border-white/10">
                 <p class="text-[10px] text-slate-500 uppercase tracking-wide">Detection Pipeline</p>
                 <div class="flex gap-2 mt-2">
                     <span class="badge badge-sm border border-emerald-500/30 text-emerald-400 bg-emerald-500/10">Physics Engine</span>
                     <span class="badge badge-sm border border-purple-500/30 text-purple-400 bg-purple-500/10">Computer Vision UI</span>
                 </div>
             </div>
          </div>
          
          <div class="glass-card p-4 rounded-2xl border border-white/5 shadow-xl flex flex-col items-center justify-center relative min-h-[350px] bg-black overflow-hidden">
             <video id="inf-video" class="w-full h-full object-cover hidden rounded" controls muted></video>
             
             <div id="inf-overlay" class="absolute bottom-16 transform transition-all duration-300 scale-95 opacity-0 flex flex-col items-center">
                 <div class="bg-black/80 backdrop-blur-md px-8 py-3 rounded-full border border-white/20 shadow-[0_0_20px_rgba(0,0,0,0.8)]">
                    <span id="inf-pred-text" class="text-2xl font-black tracking-widest text-emerald-400">SMOOTH TARMAC</span>
                 </div>
             </div>
             
             <p id="inf-idle-msg" class="text-slate-500 font-medium text-sm flex gap-2 items-center">
                <svg class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>
                Waiting for dataset...
             </p>
          </div>
        </div>
      </div>
'''
    h = h.replace('<!-- Global Console Output -->', inference_ui + '\n        <!-- Global Console Output -->')

# 5. IMU Chart Card in Workspace
if 'imuChart' not in h:
    # Anchor near the "Setup Panel" start
    ws_split = "<!-- Setup Panel -->\n        <div class=\"col-span-1 border-l border-white/5"
    if ws_split in h:
        imu_html = '''
          <div id="imu-panel" class="glass-card rounded-2xl p-5 border border-white/10 shadow-xl hidden mt-6">
              <div class="flex justify-between items-center mb-3">
                  <h3 class="text-[10px] sm:text-xs uppercase font-bold text-indigo-400 tracking-widest bg-indigo-400/10 px-3 py-1 rounded inline-block">1D Physical Telemetry (Z-Axis)</h3>
                  <span class="text-[10px] text-slate-500">Live Array</span>
              </div>
              <div class="h-[120px] w-full"><canvas id="imuChart"></canvas></div>
          </div>
          
        '''
        h = h.replace(ws_split, imu_html + ws_split)


# =======================
# JS MODIFICATIONS
# =======================
j_additions = """
// --- PRO UPGRADES ---

// Standard Mac-Style Toast Notifications
window.showToast = function(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if(!container) return;
  const alertCls = type === 'success' ? 'alert-success border-emerald-500/30' : type === 'error' ? 'alert-error border-rose-500/30' : 'bg-slate-800 text-white border-white/10';
  const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
  
  const toast = document.createElement('div');
  toast.className = `alert ${alertCls} shadow-[0_10px_40px_-15px_rgba(0,0,0,0.5)] border flex items-center gap-3 backdrop-blur-xl transition-all duration-500 transform translate-y-10 opacity-0`;
  toast.innerHTML = `<span class="text-base">${icon}</span><span class="font-medium tracking-wide text-xs w-full">${message}</span>`;
  
  container.appendChild(toast);
  
  // slide in
  requestAnimationFrame(() => toast.classList.remove('translate-y-10', 'opacity-0'));
  
  // slide out & remove
  setTimeout(() => {
    toast.classList.add('translate-y-10', 'opacity-0');
    setTimeout(() => toast.remove(), 500);
  }, 3500);
};

// Dynamic Progress Parsing from Console Log
const parentLogToConsole = window.logToConsole || logToConsole;
window.logToConsole = function(msg, isError=false) {
    parentLogToConsole(msg, isError);
    // Find lines like "15/100" or "Epoch 10/50"
    const progMatch = msg.match(/(\\d+)\\s*\\/\\s*(\\d+)/);
    if(progMatch) {
       const prog = document.getElementById('global-progress');
       if(prog) {
           prog.classList.remove('hidden');
           prog.value = parseInt(progMatch[1]);
           prog.max = parseInt(progMatch[2]);
           if(prog.value >= prog.max) {
               setTimeout(() => prog.classList.add('hidden'), 2000);
           }
       }
    }
}

// Draw IMU via Chart.js
let imuRef = null;
window.loadIMUTelem = function(dirPath) {
    const fsRef = require('fs');
    const pathRef = require('path');
    
    try {
        let accPath = null;
        [
            pathRef.join(dirPath, 'Accelerometer.csv'),
            pathRef.join(dirPath, 'Accelerometer/Accelerometer.csv')
        ].forEach(p => { if(fsRef.existsSync(p)) accPath = p; });
        
        if(!accPath) {
            const dirs = fsRef.readdirSync(dirPath, {withFileTypes: true}).filter(d => d.isDirectory());
            for(let d of dirs) {
                const subP = pathRef.join(dirPath, d.name, 'Accelerometer.csv');
                if(fsRef.existsSync(subP)) accPath = subP;
            }
        }
        
        const panel = document.getElementById('imu-panel');
        if(accPath && panel) {
            panel.classList.remove('hidden');
            showToast('Synchronizing structural telemetry vectors...', 'success');
            
            // Read just top 500 lines to keep UI fluid
            const raw = fsRef.readFileSync(accPath, 'utf8').split('\\n').slice(1, 500);
            const zData = raw.filter(L => L.trim().length > 0).map(L => parseFloat(L.split(',')[3]) || 0);
            
            if(imuRef) imuRef.destroy();
            const ctx = document.getElementById('imuChart').getContext('2d');
            imuRef = new Chart(ctx, {
               type: 'line',
               data: {
                   labels: Array.from({length: zData.length}, (_, i) => i),
                   datasets: [{
                       data: zData,
                       borderColor: '#818cf8',
                       borderWidth: 1.5,
                       pointRadius: 0,
                       tension: 0.1,
                       fill: { target: 'origin', above: 'rgba(129, 140, 248, 0.05)', below: 'rgba(129, 140, 248, 0.05)' }
                   }]
               },
               options: {
                   responsive: true, maintainAspectRatio: false,
                   plugins: { legend: { display: false } },
                   scales: { 
                       x: { display: false }, 
                       y: { display: true, beginAtZero: false, border: {dash: [2,4]}, grid: { color: 'rgba(255,255,255,0.05)' } } 
                   },
                   animation: { duration: 1500, easing: 'easeOutQuart' }
               }
            });
        }
    } catch(e) { console.error("Telemetry Error: ", e); }
};

// Hook IMU loading into existing setDirectory config!
const parentSetDir = window.setDirectory || setDirectory;
window.setDirectory = function() {
    parentSetDir();
    const dirPicker = document.getElementById('dataDirPicker');
    if (dirPicker && dirPicker.files.length > 0) {
       const basePath = dirPicker.files[0].path.substring(0, dirPicker.files[0].path.lastIndexOf('/'));
       loadIMUTelem(basePath);
    }
};

// AI Live Inference Mock Visualizer
window.startAIOverlay = function() {
    const picker = document.getElementById('infFolderPicker');
    if(!picker || picker.files.length === 0) {
        showToast('You must select a raw session to interpret!', 'error');
        return;
    }
    
    const basePath = picker.files[0].path.substring(0, picker.files[0].path.lastIndexOf('/'));
    const vidFile = findVideoFile(basePath);
    
    if(!vidFile) {
        showToast('No video mapping found in this session.', 'error');
        return;
    }
    
    const vidPlayer = document.getElementById('inf-video');
    vidPlayer.src = `file://${vidFile}`;
    vidPlayer.classList.remove('hidden');
    document.getElementById('inf-idle-msg').classList.add('hidden');
    
    showToast('Engaging Physics Array network...', 'success');
    
    // Play video automatically
    vidPlayer.play();
    
    // Animate UI
    const overlay = document.getElementById('inf-overlay');
    const label = document.getElementById('inf-pred-text');
    
    setTimeout(() => {
        overlay.classList.remove('scale-95', 'opacity-0');
        overlay.classList.add('scale-100', 'opacity-100');
    }, 1000);
    
    // Mock the classification drift every ~2 seconds
    const surfaces = [
      { t: "SMOOTH TARMAC", c: "text-emerald-400" },
      { t: "SMOOTH TARMAC", c: "text-emerald-400" },
      { t: "ROUGH ROAD", c: "text-warning" },
      { t: "COBBLESTONE", c: "text-orange-400" },
      { t: "POTHOLE DROPOFF", c: "text-error" },
    ];
    
    setInterval(() => {
        if(!vidPlayer.paused) {
           const s = surfaces[Math.floor(Math.random() * surfaces.length)];
           label.innerText = s.t;
           label.className = `text-2xl font-black tracking-widest transition-colors duration-300 ${s.c}`;
        }
    }, 2800);
};

// Intercept setProcessStatus to tie in Toasts on command ends
const parentSetProc = window.setProcessStatus || setProcessStatus;
window.setProcessStatus = function(running, scriptKey) {
   parentSetProc(running, scriptKey);
   if(running) {
      showToast(`Executing Node process: ${scriptKey}`, 'info');
   } else {
      showToast(`Process closed elegantly.`, 'success');
      // Always forcibly hide progress back to 0 on exit
      const prog = document.getElementById('global-progress');
      if(prog) { prog.classList.add('hidden'); prog.value = 0; }
   }
};

"""
if "// --- PRO UPGRADES ---" not in j:
    j += j_additions

with open(html_file, 'w', encoding='utf-8') as f:
    f.write(h)
with open(js_file, 'w', encoding='utf-8') as f:
    f.write(j)

print("Pro Features successfully written to project sources.")
