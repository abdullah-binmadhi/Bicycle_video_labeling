import os

HTML_FILE = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html"
JS_FILE = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/renderer.js"

# 1. Update HTML with telemetry viewer
with open(HTML_FILE, 'r') as f:
    html_content = f.read()
    
new_html_block = """
          <!-- Live Dual-Stream Array Results -->
          <div class="grid grid-cols-1 gap-6 mt-6">
              <div class="glass-card p-6 rounded-2xl border border-white/10 shadow-xl relative overflow-hidden bg-gradient-to-r from-slate-900 to-black">
                  <div class="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl" id="surface-glow"></div>
                  <div class="flex justify-between items-center mb-6 relative z-10 border-b border-white/5 pb-4">
                      <div>
                          <h3 class="text-emerald-400 font-bold tracking-widest text-sm uppercase flex items-center gap-2">
                              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                              TEST PHASE: Dual-Stream Physics Engine
                          </h3>
                          <p class="text-xs text-slate-400">Processing LM-17.06_multi_sensor_aligned.csv Output</p>
                      </div>
                      <button id="btn-run-testing" class="btn btn-sm btn-outline text-emerald-400 border-emerald-500/50 hover:bg-emerald-500 hover:text-white" onclick="startTestingSimulation()">
                          Execute Local Inference
                      </button>
                  </div>
                  
                  <div class="grid grid-cols-3 gap-6 relative z-10">
                      <!-- Stream 1 -->
                      <div class="space-y-1">
                          <p class="text-[10px] text-slate-500 uppercase tracking-widest">Stream 1: IMU Core Payload</p>
                          <p class="text-sm font-mono text-blue-300" id="testing-imu-state">Awaiting Feed...</p>
                      </div>
                      
                      <!-- Stream 2 -->
                      <div class="space-y-1">
                          <p class="text-[10px] text-slate-500 uppercase tracking-widest">Stream 2: 3.0Hz DSP Kinematic</p>
                          <p class="text-sm font-mono text-purple-300" id="testing-dsp-state">Awaiting Feed...</p>
                      </div>
                      
                      <!-- Final Classification -->
                      <div class="space-y-1 bg-black/40 p-3 rounded-xl border border-white/5">
                          <p class="text-[10px] text-emerald-500/70 uppercase tracking-widest">Live Meta-Classification</p>
                          <p class="text-2xl font-black text-emerald-400" id="testing-prediction">STANDBY</p>
                          <p class="text-[10px] text-slate-400 font-mono mt-1" id="testing-confidence">Conf: 0.00%</p>
                      </div>
                  </div>
              </div>
          </div>
"""

# Inject before closing of view-inference
if "<!-- Live Dual-Stream Array Results -->" not in html_content:
    html_content = html_content.replace(
        '<!-- NEW: Real-Time Advanced Telemetry Array (Features 3, 4, 5) -->',
        new_html_block + '\n          <!-- NEW: Real-Time Advanced Telemetry Array (Features 3, 4, 5) -->'
    )
    with open(HTML_FILE, 'w') as f:
        f.write(html_content)

# 2. Update JS
with open(JS_FILE, 'r') as f:
    js_content = f.read()

injector_code = """
window.startTestingSimulation = function() {
    console.log("Starting Testing Simulation Engine...");
    
    // Simulate reading the JSON output generated
    const fs = require('fs');
    const path = require('path');
    
    // This expects the file we generated via run_inference.py
    const pFile = path.join(__dirname, '..', 'predictions.json');
    let predictions = [];
    try {
        const data = fs.readFileSync(pFile, 'utf8');
        predictions = JSON.parse(data);
    } catch(e) {
        showToast('Run ML Inference backend script first!', 'error');
        return;
    }
    
    showToast('Injecting dataset bounds (LM-17.06)...', 'success');
    document.getElementById('btn-run-testing').innerHTML = 'Processing...';
    document.getElementById('btn-run-testing').disabled = true;
    
    let step = 0;
    const interval = setInterval(() => {
        if(step >= predictions.length) {
            clearInterval(interval);
            showToast('Testing sequence completed!', 'success');
            document.getElementById('btn-run-testing').innerHTML = 'Execute Local Inference';
            document.getElementById('btn-run-testing').disabled = false;
            return;
        }
        
        const current = predictions[step];
        
        // Update UI
        document.getElementById('testing-prediction').innerText = current.surface.toUpperCase();
        document.getElementById('testing-confidence').innerText = `Conf: ${current.confidence.toFixed(2)}% | Var: ${current.variance_metric.toFixed(4)}`;
        
        document.getElementById('testing-imu-state').innerText = `[TS: ${current.timestamp}s] Tensor(1, 50, 6)`;
        document.getElementById('testing-dsp-state').innerText = `[Filtered] Tensor(1, 50, 6)`;
        
        // Glow effect based on surface
        const glow = document.getElementById('surface-glow');
        if(current.surface.includes('Asphalt')) {
            glow.className = "absolute top-0 right-0 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl";
            document.getElementById('testing-prediction').className = "text-2xl font-black text-emerald-400";
        } else if(current.surface.includes('Gravel')) {
            glow.className = "absolute top-0 right-0 w-64 h-64 bg-yellow-500/10 rounded-full blur-3xl";
            document.getElementById('testing-prediction').className = "text-2xl font-black text-yellow-400";
        } else {
            glow.className = "absolute top-0 right-0 w-64 h-64 bg-rose-500/10 rounded-full blur-3xl";
            document.getElementById('testing-prediction').className = "text-2xl font-black text-rose-400";
        }
        
        step++;
    }, 1000); // 1 update per second
};
"""

if "window.startTestingSimulation" not in js_content:
    js_content += "\n" + injector_code
    with open(JS_FILE, 'w') as f:
        f.write(js_content)

print("Injected Testing Viewer into Electron UI.")
