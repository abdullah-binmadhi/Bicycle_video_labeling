const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Path relative to the electron executable CWD
let pythonPath = 'python3';
const preferredPython = '/Library/Frameworks/Python.framework/Versions/3.14/bin/python3';
if (require('fs').existsSync(preferredPython)) {
    pythonPath = preferredPython;
}

// Dynamically locate root based on execution context (raw vs macOS App bundle)
let rootDir = path.join(__dirname, '../../');
if (__dirname.includes('Contents/Resources/app')) {
  rootDir = path.join(__dirname, '../../../../../../');
}

const scripts = {
  'extract': path.join(rootDir, 'data_pipeline/frame_extractor.py'),
  'roboflow': path.join(rootDir, 'data_pipeline/roboflow_manager.py'),
  'clip': path.join(rootDir, 'data_pipeline/yolo_clip_auto.py'),
  'sync': path.join(rootDir, 'data_pipeline/synchronizer.py'),
  'train': path.join(rootDir, 'train_unified.py'),
  'inference': path.join(rootDir, 'run_inference.py')
};

let activeProcess = null;

// UI Helpers
window.stopActiveProcess = function() {
    if (activeProcess) {
        logToConsole(`\n[WARN] Force stopping active process (PID: ${activeProcess.pid})...\n`, true);
        activeProcess.kill('SIGINT');
        activeProcess = null;
    } else {
        logToConsole("[WARN] No active process to stop.\n", true);
    }
};

function switchView(viewName) {
  // Update navs
  document.querySelectorAll('.menu a').forEach(el => el.classList.remove('active'));
  document.getElementById(`nav-${viewName}`).classList.add('active');

  // Update views
  document.querySelectorAll('[id^="view-"]').forEach(el => el.classList.add('hidden-view'));
  document.getElementById(`view-${viewName}`).classList.remove('hidden-view');
}

function findVideoFile(dir) {
  if (!fs.existsSync(dir)) return null;
  try {
      const files = fs.readdirSync(dir, { withFileTypes: true });
      
      // 1. Check direct children first
      for (let file of files) {
        if (file.isFile() && file.name.match(/\.(mp4|mov|avi|mkv)$/i)) {
          return path.join(dir, file.name);
        }
      }
      
      // 2. Check one level deep (e.g. if user selected "Android" OS folder containing Session folders)
      for (let file of files) {
        if (file.isDirectory()) {
          const subDir = path.join(dir, file.name);
          const subFiles = fs.readdirSync(subDir, { withFileTypes: true });
          for (let subFile of subFiles) {
             if (subFile.isFile() && subFile.name.match(/\.(mp4|mov|avi|mkv)$/i)) {
               return path.join(subDir, subFile.name);
             }
          }
        }
      }
  } catch (err) {
      console.error("Error reading directories:", err);
  }
  return null;
}

function setDirectory() {
  const dirPath = document.getElementById('annoDirPath') ? document.getElementById('annoDirPath').value : "";
  const label = document.getElementById('selectedDirLabel');
  if (dirPath && dirPath.trim() !== "") {
    const basePath = dirPath;
    if(label) label.innerText = `Mapped Base Path: ${basePath}`;
    logToConsole(`Workspace path updated: ${basePath}`);

    // Try finding a video preview to show
    const videoFile = findVideoFile(basePath);
    const videoCard = document.getElementById('video-preview-card');
    const videoPlayer = document.getElementById('video-player');
    const videoPathLabel = document.getElementById('video-path-label');

    if (videoFile && videoCard && videoPlayer) {
        videoPlayer.src = `file://${videoFile}`;
        if(videoPathLabel) videoPathLabel.innerText = `Previewing Local File: .../${path.basename(path.dirname(videoFile))}/${path.basename(videoFile)}`;
        videoCard.classList.remove('hidden');
        logToConsole(`Found session video for preview: ${path.basename(videoFile)}`);
    } else if (videoCard) {
        videoCard.classList.add('hidden');
    }
  }
}

function setVideoFile() {
  const videoPath = document.getElementById('annoVideoPath') ? document.getElementById('annoVideoPath').value : "";
  if (videoPath && videoPath.trim() !== "") {
      const videoCard = document.getElementById('video-preview-card');
      const videoPlayer = document.getElementById('video-player');
      const videoPathLabel = document.getElementById('video-path-label');
      
      if(videoPlayer && videoCard) {
        videoPlayer.src = `file://${videoPath}`;
        if(videoPathLabel) videoPathLabel.innerText = `Previewing Local File: ${path.basename(videoPath)}`;
        videoCard.classList.remove('hidden');
        logToConsole(`Manually mapped master video: ${path.basename(videoPath)}`);
      }
  }
}

function logToConsole(message, isError = false) {
  const consoleDisplay = document.getElementById('console-output');
  
  // Use Tailwind or custom green/red text colors for clarity
  let colorClass = 'text-green-400'; // Default green for successful operations 
  
  // Try to heuristically force obvious info/success messages to green 
  // even if they came via Python's default stderr logging stream.
  if (isError) {
    if (message.includes('INFO') || message.includes('Loaded') || message.includes('Success') || message.includes('100%')) {
         colorClass = 'text-green-400';
    } else {
         colorClass = 'text-red-400'; // Real errors are red
    }
  }

  consoleDisplay.innerHTML += `<span class="${colorClass}">${message}</span>`;
  consoleDisplay.scrollTop = consoleDisplay.scrollHeight;
  
  if (message.includes("Extracted ") && message.includes(" frames")) {
    document.getElementById('extract-progress-container').classList.remove('hidden');
    
    // Check if we have fractional progress format like "Extracted 100/1234 frames..."
    const fractionsMatch = message.match(/Extracted\s+(\d+)\/(\d+)\s+frames/i);
    let progressStr = message.trim();
    
    if (fractionsMatch) {
      const current = parseInt(fractionsMatch[1]);
      const total = parseInt(fractionsMatch[2]);
      const pct = Math.round((current / total) * 100);
      progressStr = `Generating: ${current} / ${total} Frames...`;
      
      const realProgressBar = document.getElementById('extract-progress-bar');
      if (realProgressBar) {
        realProgressBar.value = pct;
        realProgressBar.classList.remove('hidden');
      }
    } else {
      progressStr = "Generating: " + progressStr;
    }
    
    document.getElementById('extract-progress-text').innerText = progressStr;
  }

  // Custom parsing for UI updates (e.g. Training stats updates)
  if (message.includes("Epoch [") || message.includes("Epoch ")) {
    document.getElementById('training-stats').classList.remove('hidden');
    // Extract format: "Epoch [1/10]" or "Epoch 1/10"
    const epochMatch = message.match(/Epoch\s*\[?\s*(\d+)\s*\/\s*(\d+)/i);
    const lossMatch = message.match(/Loss:\s*([0-9.]+)/i);
    if (epochMatch) {
      document.getElementById('stat-epoch').innerText = `${epochMatch[1]} / ${epochMatch[2]}`;
      const current = parseInt(epochMatch[1]);
      const total = parseInt(epochMatch[2]);
      const progressPercent = (current / total) * 100;
      document.getElementById('stat-progress').value = progressPercent;
    }
    if (lossMatch) document.getElementById('stat-loss').innerText = lossMatch[1];
  }
}

function setProcessStatus(running, scriptKey) {
  const btn = document.getElementById("btn-" + scriptKey);
  const spinner = document.getElementById("spinner-" + scriptKey);
  const activeDot = document.getElementById("status-indicator-active");
  const idleDot = document.getElementById("status-indicator-idle");
  const statusText = document.getElementById("status-text");

  if (running) {
    if (btn) btn.disabled = true;
    if (spinner) spinner.classList.remove("hidden");
    if (activeDot) activeDot.classList.remove("hidden");
    if (idleDot) idleDot.classList.add("hidden");
    if (statusText) statusText.innerText = "Running " + scriptKey + "...";
    
    const stopBtn = document.getElementById("btn-stop-" + scriptKey);
    if (stopBtn) stopBtn.classList.remove("hidden");
  } else {
    if (btn) btn.disabled = false;
    if (spinner) spinner.classList.add("hidden");
    if (activeDot) activeDot.classList.add("hidden");
    if (idleDot) idleDot.classList.remove("hidden");
    if (statusText) statusText.innerText = "Ready";
    
    const stopBtn = document.getElementById("btn-stop-" + scriptKey);
    if (stopBtn) stopBtn.classList.add("hidden");

    if (scriptKey === "extract") {
      const prog = document.getElementById("extract-progress-container");
      if (prog) prog.classList.add("hidden");
    }
  }
}

function stopProcess() {
  if (activeProcess) {
    logToConsole("\n[WARN] Stopping execution manually...\n", true);
    activeProcess.kill("SIGINT");
    const prog = document.getElementById("extract-progress-container");
    if (prog) prog.classList.add("hidden");
  }
}

function runScript(scriptKey) {
  try {
    logToConsole("[SUCCESS] Starting script execution for: " + scriptKey);
    _runScript(scriptKey);
  } catch(e) {
    logToConsole("[WARN] App Error: " + e.toString() + "<br/>" + e.stack, true);
  }
}

function _runScript(scriptKey) {
  if (activeProcess) {
    logToConsole("[WARN] A process is already running. Please wait.\\n", true);
    return;
  }

  const targetScript = scripts[scriptKey];
  
  if (!fs.existsSync(targetScript)) {
    logToConsole(`[WARN] Error: Script not found at ${targetScript}. Check paths.\\n`, true);
    return;
  }

  // Parse custom args if it's the extract step
  let args = ['-u', targetScript];
  if (scriptKey === 'clip') {
     const dirPath = document.getElementById('annoDirPath') ? document.getElementById('annoDirPath').value : "";
     if(!dirPath) {
         logToConsole("[WARN] Please select an Image Extracted Folder first.\n", true);
         return;
     }
     
     args.push('--frames_dir', dirPath);
     
     const customOutPath = document.getElementById('clipCustomOutPath') ? document.getElementById('clipCustomOutPath').value.trim() : "";
     if (customOutPath) {
         args.push('--output_csv', path.join(customOutPath, 'Label.0.csv'));
     } else {
         // Default back to native Label.0.csv inside that session
         args.push('--output_csv', path.join(dirPath, '../Label/Label.0.csv'));
     }

     const selectedClasses = [];
     document.querySelectorAll('.clip-class-checkbox:checked').forEach(cb => {
         selectedClasses.push(cb.value);
     });
     if (selectedClasses.length > 0) {
         args.push('--classes', ...selectedClasses);
     }
  }
  if (scriptKey === 'extract') {
    const extractVideoPathValue = document.getElementById('extractVideoPath') ? document.getElementById('extractVideoPath').value.trim() : "";
      const customOutPath = document.getElementById('extractCustomOutPath') ? document.getElementById('extractCustomOutPath').value.trim() : "";
      const startTimeEl = document.getElementById('extractStartTime');
      const startTimeOverride = startTimeEl ? startTimeEl.value : "";
      
      if (!extractVideoPathValue) {
        logToConsole("[WARN] Please select a video file to extract frames from.\n", true);
        return;
      }
      const videoPath = extractVideoPathValue;
      let outDir = "";
      
      if (customOutPath !== "") {
        logToConsole(`ℹ️ Using custom output directory: ${customOutPath}\\n`);
        outDir = customOutPath;
        if (!fs.existsSync(outDir)) { fs.mkdirSync(outDir, { recursive: true }); }
      } else {
        logToConsole("ℹ️ Output directory not explicitly set. Defaulting to 'VideoFrames' folder.\\n");
        outDir = path.join(rootDir, 'VideoFrames');
        if (!fs.existsSync(outDir)) { fs.mkdirSync(outDir, { recursive: true }); }
      }
    args.push('--video', videoPath);
    args.push('--out_dir', outDir);

    if (startTimeOverride.trim() !== '') {
      args.push('--start_time', startTimeOverride.trim());
    }
  }
  
  if (scriptKey === 'sync') {
      // 1. Data Source
      const sourceType = document.querySelector('input[name="sync-source-type"]:checked').value;
      if (sourceType === 'global') {
          const customDataDir = document.getElementById('syncDataPath') ? document.getElementById('syncDataPath').value.trim() : "";
          if (customDataDir) {
              args.push('--data_dir', customDataDir);
          }
      } else {
          args.push('--adhoc');
          const imu = document.getElementById('adhocImuPath').value.trim();
          const label = document.getElementById('adhocLabelPath').value.trim();
          if (!imu || !label) {
              logToConsole("[WARN] Ad-Hoc sync requires both IMU and Label CSVs.\n", true);
              return;
          }
          args.push('--imu_csv', imu);
          args.push('--label_csv', label);
      }

      // 2. Tolerance Slider
      const tol = document.getElementById('sync-tolerance-slider').value;
      args.push('--tolerance', tol);
      
      // 3. Gap Handling
      const gapHandling = document.getElementById('sync-gap-handling').value;
      args.push('--gap_handling', gapHandling);
      
      // 4. DSP Filter Toggle
      const applyDsp = document.getElementById('toggle-dsp').checked;
      if (applyDsp) {
         args.push('--apply_dsp');
      }

      // Show Analytics Dashboard Reset
      document.getElementById('sync-analytics-board').classList.add('hidden');
      document.getElementById('sync-stat-rows').innerText = "0";
      document.getElementById('sync-stat-drops').innerText = "0%";
      document.getElementById('sync-stat-classes').innerHTML = "";
  }

    if (scriptKey === 'train') {
        const customTrainData = document.getElementById('trainDataPath') ? document.getElementById('trainDataPath').value.trim() : "";
        if (customTrainData) args.push('--data', customTrainData);
        
        const useVision = document.getElementById('toggle-vision')?.checked ?? false;
        const useImu = document.getElementById('toggle-imu')?.checked ?? true;
        
        const epochs = document.getElementById('train-epochs')?.value;
        const lr = document.getElementById('train-lr')?.value;
        const batch = document.getElementById('train-batch')?.value;
        const checkpoint = document.getElementById('trainResumePath')?.value;

        args.push('--use_vision', useVision ? 'True' : 'False');
        args.push('--use_imu', useImu ? 'True' : 'False');
        
        if (epochs) args.push('--epochs', epochs);
        if (lr) args.push('--lr', lr);
        if (batch) args.push('--batch_size', batch);
        if (checkpoint) args.push('--checkpoint', checkpoint);

        const stopBtn = document.getElementById('btn-train-stop');
        if (stopBtn) stopBtn.classList.remove('hidden');
        const statsBoard = document.getElementById('training-stats');
        if (statsBoard) statsBoard.style.display = 'grid';
        if (window.initLossChart) window.initLossChart();
    }

    logToConsole(`\n$ python3 ${path.basename(targetScript)} ${args.slice(1).join(' ')}\n`);
    setProcessStatus(true, scriptKey);

    // Spawn the python process inside the workspace root so paths in config resolve
    const cwdPath = path.join(__dirname, '../../');
  
  // Inject common macOS paths so packaged Electron apps can find python3
  const customEnv = Object.assign({}, process.env, {
    PATH: (process.env.PATH || '') + ':/Library/Frameworks/Python.framework/Versions/3.14/bin:/opt/homebrew/bin:/usr/local/bin'
  });
  
  activeProcess = spawn(pythonPath, args, { cwd: cwdPath, env: customEnv });

  activeProcess.stdout.on('data', (data) => {
    logToConsole(data.toString());
  });

  activeProcess.stderr.on('data', (data) => {
    logToConsole(data.toString(), true);
  });

  activeProcess.on('error', (err) => {
    logToConsole(`[WARN] Process Execution Error: ${err.message}\n`, true);
    setProcessStatus(false, scriptKey);
    activeProcess = null;
  });

  activeProcess.on('close', (code) => {
    logToConsole(`\\n> Process exited with code ${code}\\n`);
    setProcessStatus(false, scriptKey);
    activeProcess = null;
  });
}


let consoleOpen = true;
window.toggleConsole = function() {
  const wrapper = document.getElementById('console-wrapper');
  const chevron = document.getElementById('console-chevron');
  consoleOpen = !consoleOpen;
  if (consoleOpen) {
    wrapper.style.height = '220px';
    if(chevron) chevron.style.transform = 'rotate(0deg)';
  } else {
    wrapper.style.height = '0px';
    if(chevron) chevron.style.transform = 'rotate(180deg)';
  }
};

let settingsOpen = false;
window.toggleSettings = function() {
  const panel = document.getElementById('settings-panel');
  if (!panel) return;
  
  settingsOpen = !settingsOpen;
  if (settingsOpen) {
    panel.classList.remove('translate-x-full');
  } else {
    panel.classList.add('translate-x-full');
  }
};


// --- ADVANCED FEATURES ---

// KILL PROCESS
window.killProcess = function() {
  if (activeProcess) {
    logToConsole('\n[System] Sending INTERRUPT signal to abort process...\n', true);
    activeProcess.kill('SIGKILL');
  }
};

// PERSISTENT SETTINGS CONFIG
const settingInputs = [
  'rfApiKey', 'rfWorkspace', 'rfProject', 'rfVersion', 
  'confLR', 'confBatchSize', 'confEpochs', 
  'extractStartTime' // Add more IDs here as needed
];

function saveSettings() {
  settingInputs.forEach(id => {
    const el = document.getElementById(id);
    if(el && el.value !== undefined) {
      localStorage.setItem('cyclesafe_' + id, el.value);
    }
  });
  logToConsole('[System] Settings saved to local cache.\n');
}

function loadSettings() {
  settingInputs.forEach(id => {
    const el = document.getElementById(id);
    if(el) {
      const savedVal = localStorage.getItem('cyclesafe_' + id);
      if(savedVal !== null && savedVal !== '') {
        el.value = savedVal;
      }
      
      // Auto-save on edit
      el.addEventListener('change', saveSettings);
    }
  });
}

// Ensure the UI settings are loaded when ready and the Save Config button manually persists
document.addEventListener('DOMContentLoaded', () => {
  loadSettings();
  
  // Attach save to the Save Configuration button
  const saveBtn = document.getElementById('btn-save-config');
  if(saveBtn) {
    saveBtn.addEventListener('click', saveSettings);
  }
});

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
    const progMatch = msg.match(/(\d+)\s*\/\s*(\d+)/);
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
            const raw = fsRef.readFileSync(accPath, 'utf8').split('\n').slice(1, 500);
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

// --- Phase 2 Globals ---
let infMap = null;
let threeScene = null, threeCamera = null, threeRenderer = null, threeCube = null;

function initLeaflet(lat=52.5200, lng=13.4050) {
    if(!infMap) {
        const mapContainer = document.getElementById('inf-map');
        if(!mapContainer) return;
        
        infMap = L.map('inf-map').setView([lat, lng], 16);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap',
            subdomains: 'abcd',
            maxZoom: 20
        }).addTo(infMap);
    }
}

function initThreeJS() {
    if(threeRenderer) return;
    const container = document.getElementById('inf-3d-canvas');
    if(!container) return;
    container.innerHTML = ''; // clear text
    
    threeScene = new THREE.Scene();
    threeCamera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    
    threeRenderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    threeRenderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(threeRenderer.domElement);
    
    // Create a bike/phone stand-in geometry
    const geometry = new THREE.BoxGeometry(2, 0.5, 4);
    
    // Fancy wireframe + material
    const material = new THREE.MeshBasicMaterial( { color: 0xf59e0b, wireframe: true } );
    threeCube = new THREE.Mesh(geometry, material);
    threeScene.add(threeCube);
    
    threeCamera.position.z = 5;
    threeCamera.position.y = 2;
    threeCamera.lookAt(0,0,0);
    
    // Add grid helper
    const gridHelper = new THREE.GridHelper(10, 10, 0x475569, 0x1e293b);
    threeScene.add(gridHelper);
    
    function animate() {
        requestAnimationFrame(animate);
        threeRenderer.render(threeScene, threeCamera);
    }
    animate();
    
    // Handle resize
    window.addEventListener('resize', () => {
        if(!threeCamera || !container.clientWidth) return;
        threeCamera.aspect = container.clientWidth / container.clientHeight;
        threeCamera.updateProjectionMatrix();
        threeRenderer.setSize(container.clientWidth, container.clientHeight);
    });
}

window.startAIOverlay = function() {
    const vidPathEl = document.getElementById('infVideoPath');
    if(!vidPathEl || !vidPathEl.value.trim()) {
        showToast('You must select a Reference Video mapping first!', 'error');
        return;
    }
    
    const vidFile = vidPathEl.value.trim();
    
    const vidPlayer = document.getElementById('inf-video');
    vidPlayer.src = `file://${vidFile}`;
    vidPlayer.classList.remove('hidden');
    const idleMsg = document.getElementById('inf-idle-msg');
    if(idleMsg) idleMsg.classList.add('hidden');
    
    showToast('Engaging Physics Array network...', 'success');
    
    // Init Phase 2 components
    setTimeout(() => {
        if(typeof initLeaflet === 'function') initLeaflet();
        if(typeof initThreeJS === 'function') initThreeJS();
        
        // Setup static mock path trace
        if(typeof infMap !== 'undefined' && infMap) {
            const startLat = 52.5200;
            const startLng = 13.4050;
            const latlngs = [];
            let curl = startLat, curlg = startLng;
            for(let i=0; i<50; i++) {
                latlngs.push([curl, curlg]);
                curl += (Math.random() - 0.5) * 0.001;
                curlg += (Math.random() - 0.5) * 0.001;
            }
            L.polyline(latlngs, {color: '#10b981', weight: 4}).addTo(infMap);
            infMap.fitBounds(L.latLngBounds(latlngs));
            setTimeout(() => infMap.invalidateSize(), 500);
        }
    }, 500);
    
    // Play video automatically
    vidPlayer.play();
    if(typeof initScrubber === 'function') initScrubber(vidPlayer);
    
    // Animate UI
    const overlay = document.getElementById('inf-overlay');
    if(overlay) {
        overlay.classList.remove('scale-95', 'opacity-0');
        overlay.classList.add('scale-100', 'opacity-100');
    }
    
    // Load Predictions
    const label = document.getElementById('inf-pred-text');
    let predictions = [];
    try {
        const predPath = require('path').join(__dirname, '../../predictions.json');
        if (require('fs').existsSync(predPath)) {
            predictions = JSON.parse(require('fs').readFileSync(predPath, 'utf8'));
        }
    } catch(err) {
        console.error("Error loading predictions.json", err);
    }

    if (window.aiInterval) clearInterval(window.aiInterval);
    window.aiInterval = setInterval(() => {
        if(!vidPlayer.paused && predictions.length > 0) {
           const currentTime = vidPlayer.currentTime; // seconds
           // Find matching prediction based on timestamp
           const currentPred = predictions.find(p => p.timestamp <= currentTime && (p.timestamp + 1) > currentTime);
           
           if(currentPred) {
               label.innerText = currentPred.surface.toUpperCase();
               if(currentPred.surface.includes("Asphalt")) label.className = "text-2xl font-black tracking-widest text-emerald-400 switch-anim";
               else if(currentPred.surface.includes("Grass")) label.className = "text-2xl font-black tracking-widest text-warning switch-anim";
               else label.className = "text-2xl font-black tracking-widest text-rose-400 switch-anim";
           }
        }
    }, 500); // Check half-second ticks
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
      
      if(scriptKey === 'inference') {
         const btnInf = document.getElementById('btn-run-inf');
         if(btnInf) btnInf.classList.remove('hidden');
         showToast('Inference Array loaded! You can now Launch Visualization.', 'success');
      }
   }
};




// --- Phase 1: Analytics & Reports ---
let confChart = null, radarChart = null, driftChart = null;
let scrubberInterval = null;

function initAnalytics() {
    // 1. Confusion Matrix
    const ctxConf = document.getElementById('confusion-canvas');
    if(ctxConf && !confChart) {
        // Simple mock of a confusion matrix using a scatter/bubble or bar 
        // For actual matrix we usually use a specialized plugin or a table, but a generic bar chart works for mockup
        confChart = new Chart(ctxConf, {
            type: 'bar',
            data: {
                labels: ['Tarmac', 'Gravel', 'Cobble', 'Pothole'],
                datasets: [{
                    label: 'True Positives',
                    data: [98, 85, 92, 76],
                    backgroundColor: 'rgba(16, 185, 129, 0.6)'
                }, {
                    label: 'False Negatives',
                    data: [2, 15, 8, 24],
                    backgroundColor: 'rgba(244, 63, 94, 0.6)'
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: { stacked: true }, x: { stacked: true } }
            }
        });
    }

    // 2. Radar Chart (Precision/Recall)
    const ctxRadar = document.getElementById('radar-canvas');
    if(ctxRadar && !radarChart) {
        radarChart = new Chart(ctxRadar, {
            type: 'radar',
            data: {
                labels: ['F1-Score', 'Precision', 'Recall', 'Latency', 'Robustness'],
                datasets: [{
                    label: 'CoreML Export (iOS)',
                    data: [0.91, 0.88, 0.94, 0.99, 0.85],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.2)'
                }, {
                    label: 'TorchScript (Android)',
                    data: [0.89, 0.90, 0.86, 0.90, 0.88],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.2)'
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { r: { angleLines: { color: 'rgba(255,255,255,0.1)' }, grid: { color: 'rgba(255,255,255,0.1)' } } }
            }
        });
    }

    // 3. Drift Canvas
    const ctxDrift = document.getElementById('drift-canvas');
    if(ctxDrift && !driftChart) {
        driftChart = new Chart(ctxDrift, {
            type: 'line',
            data: {
                labels: Array.from({length: 50}, (_, i) => i),
                datasets: [{
                    label: 'Run A',
                    data: Array.from({length: 50}, () => Math.random() * 2 + 1),
                    borderColor: '#8b5cf6', borderWidth: 2, tension: 0.4
                }, {
                    label: 'Run B',
                    data: Array.from({length: 50}, () => Math.random() * 2.2 + 0.8),
                    borderColor: '#f43f5e', borderWidth: 2, tension: 0.4
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }
}

// Ensure it initializes when switching tabs
const oldSwitchView = window.switchView;
window.switchView = function(viewId) {
    oldSwitchView(viewId);
    if(viewId === 'view-analytics') {
        setTimeout(initAnalytics, 100);
    }
}

window.generatePDFReport = function() {
    showToast('Compiling analytical snapshot...', 'info');
    const elem = document.getElementById('view-analytics');
    
    // HTML2PDF settings
    const opt = {
      margin:       1,
      filename:     'CycleSafe_Report.pdf',
      image:        { type: 'jpeg', quality: 0.98 },
      html2canvas:  { scale: 2, useCORS: true },
      jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
    };
    
    html2pdf().set(opt).from(elem).save().then(() => {
        showToast('PDF Exported Successfully!', 'success');
    });
};

// --- Scrubber & FFT Mock ---
function initScrubber(videoPlayer) {
    const scrubber = document.getElementById('inf-scrubber');
    const fftCanvas = document.getElementById('fft-canvas');
    if(!scrubber || !fftCanvas) return;
    
    const ctx = fftCanvas.getContext('2d');
    
    // Mock FFT Bars
    function drawFFT() {
        if(videoPlayer.paused) return;
        ctx.clearRect(0, 0, fftCanvas.width, fftCanvas.height);
        const barWidth = 4;
        const totalBars = Math.floor(fftCanvas.width / (barWidth + 1));
        
        ctx.fillStyle = '#10b981'; // Emerald
        for(let i = 0; i < totalBars; i++) {
            const h = Math.random() * fftCanvas.height;
            ctx.fillRect(i * (barWidth + 1), fftCanvas.height - h, barWidth, h);
        }
    }
    
    if(scrubberInterval) clearInterval(scrubberInterval);
    scrubberInterval = setInterval(() => {
        if(!videoPlayer.paused && videoPlayer.duration) {
            const progress = (videoPlayer.currentTime / videoPlayer.duration) * 100;
            scrubber.value = progress;
            drawFFT();
            
            
            
            
        }
    }, 100);
    
    scrubber.addEventListener('input', (e) => {
        if(videoPlayer.duration) {
            videoPlayer.currentTime = (e.target.value / 100) * videoPlayer.duration;
        }
    });
}







window.addEventListener("error", (event) => {
    logToConsole("ERROR: " + event.message + "<br/>" + event.filename + ":" + event.lineno, true);
});


window.previewExtractVideo = function() {
    const inputPath = document.getElementById('extractVideoPath') ? document.getElementById('extractVideoPath').value : "";
    if (inputPath) {
        logToConsole("ℹ️ Validated Video ready to map: " + inputPath);
    }
};

window.chooseOutputDir = async function() {
    const { ipcRenderer } = require('electron');
    const path = await ipcRenderer.invoke('dialog:openDirectory');
    if (path) {
        document.getElementById('extractCustomOutPath').value = path;
        logToConsole("ℹ️ Selected Output Directory: " + path);
    }
};

window.chooseVideoFile = async function() {
    const { ipcRenderer } = require('electron');
    const path = await ipcRenderer.invoke('dialog:openFile');
    if (path) {
        document.getElementById('extractVideoPath').value = path;
        logToConsole("ℹ️ Selected Video File: " + path);
        previewExtractVideo();
    }
};


window.chooseAnnoDir = async function() {
    const { ipcRenderer } = require('electron');
    const dir = await ipcRenderer.invoke('dialog:openDirectory');
    if (dir) {
        document.getElementById('annoDirPath').value = dir;
        setDirectory();
    }
};

window.chooseAnnoVideo = async function() {
    const { ipcRenderer } = require('electron');
    const file = await ipcRenderer.invoke('dialog:openFile');
    if (file) {
        document.getElementById('annoVideoPath').value = file;
        setVideoFile();
    }
};

window.chooseClipOutDir = async function() {
    const { ipcRenderer } = require('electron');
    const dir = await ipcRenderer.invoke('dialog:openDirectory');
    if (dir) {
        document.getElementById('clipCustomOutPath').value = dir;
    }
};


window.chooseAdhocImu = async function() {
    const { ipcRenderer } = require('electron');
    const file = await ipcRenderer.invoke('dialog:openCSV');
    if (file) { document.getElementById('adhocImuPath').value = file; }
};
window.chooseAdhocLabel = async function() {
    const { ipcRenderer } = require('electron');
    const file = await ipcRenderer.invoke('dialog:openCSV');
    if (file) { document.getElementById('adhocLabelPath').value = file; }
};

window.chooseSyncDir = async function() {
    const { ipcRenderer } = require('electron');
    const dir = await ipcRenderer.invoke('dialog:openDirectory');
    if (dir) {
        document.getElementById('syncDataPath').value = dir;
    }
};
  window.chooseTrainData = async function() {
      const { ipcRenderer } = require('electron');
      const file = await ipcRenderer.invoke('dialog:openCSV');
      if (file) {
          document.getElementById('trainDataPath').value = file;
      }
  };
// --- Inference Setup & Handlers ---
window.chooseInfModel = async function() {
  const { ipcRenderer } = require('electron');
  const filePath = await ipcRenderer.invoke('dialog:openModel');
  if (filePath) document.getElementById('infModelPath').value = filePath;
};

window.chooseInfCsv = async function() {
  const { ipcRenderer } = require('electron');
  const filePath = await ipcRenderer.invoke('dialog:openCSV');
  if (filePath) document.getElementById('infCsvPath').value = filePath;
};

window.chooseInfVideo = async function() {
  const { ipcRenderer } = require('electron');
  const filePath = await ipcRenderer.invoke('dialog:openVideo');
  if (filePath) {
    document.getElementById('infVideoPath').value = filePath;
    document.getElementById('inf-video').src = `file://${filePath}`;
  }
};

// --- App-Based Annotation & Canvas ---

// 1. Interactive CLIP Search Handlers
window.triggerInteractiveClip = function() {
  const promptInput = document.getElementById('interactive-clip-prompt');
  const videoPlayer = document.getElementById('video-player');
  
  if (!promptInput.value) {
      showToast('Please type a search phrase first.', 'error');
      return;
  }
  
  if (!videoPlayer || !videoPlayer.src) {
      showToast('Please map a master video first prior to searching frames.', 'error');
      return; 
  }
  
  const currentTime = videoPlayer.currentTime;
  const promptTxt = promptInput.value;
  const videoPath = document.getElementById('annoVideoPath').value;
  
  logToConsole(`[Interactive Search] Triggering specialized zero-shot inference for: "${promptTxt}" @ ${currentTime.toFixed(3)}s`);
  document.getElementById('spinner-clip-interactive').classList.remove('hidden');
  
  const { spawn } = require('child_process');
  const path = require('path');
  const fs = require('fs');
  const interactiveScript = path.join(__dirname, '../../data_pipeline/clip_interactive.py');
  
  // Choose python env
  const pythonPath = fs.existsSync(path.join(__dirname, '../../venv/bin/python')) 
    ? path.join(__dirname, '../../venv/bin/python') 
    : 'python3';
    
  const child = spawn(pythonPath, [
      interactiveScript,
      '--video', videoPath,
      '--time', currentTime.toString(),
      '--prompt', promptTxt
  ]);

  let outputData = '';
  
  child.stdout.on('data', (data) => {
      outputData += data.toString();
  });
  
  child.stderr.on('data', (data) => {
      console.warn('Interactive CLIP STDERR:', data.toString());
  });
  
  child.on('close', (code) => {
      document.getElementById('spinner-clip-interactive').classList.add('hidden');
      
      if (code !== 0) {
          showToast('Inference failed.', 'error');
          logToConsole('[Interactive Search] Inference failed (Script error).');
          return;
      }
      
      try {
          const res = JSON.parse(outputData.trim().split('\n').pop()); // last line
          if (res.error) {
              showToast(res.error, 'error'); return;
          }
          if (res.success) {
              logToConsole(`[Interactive Search] Identified "${promptTxt}" cluster! Score: ${res.score.toFixed(3)}`);
              
              const box = res.box; // [x, y, w, h] in original video dimensions
              const videoWidth = res.original_width;
              const videoHeight = res.original_height;
              
              drawBoundingBox(promptTxt, box, videoWidth, videoHeight);
              
              // Automatically save to manual_annotations.csv
              const csvPath = path.join(__dirname, '../../manual_annotations.csv');
              
              if (!fs.existsSync(csvPath)) {
                  fs.writeFileSync(csvPath, "video,timestamp,x,y,w,h,label,confidence\n");
              }
              
              const row = `${videoPath},${currentTime.toFixed(3)},${box[0]},${box[1]},${box[2]},${box[3]},${promptTxt},1.0\n`;
              fs.appendFileSync(csvPath, row);
              logToConsole(`Saved point data to ${csvPath}`);
          }
      } catch (err) {
          showToast('Failed to parse Python response', 'error');
          console.error(err, outputData);
      }
  });
}

function drawBoundingBox(label, boxCoords, rawVidW, rawVidH) {
    const canvas = document.getElementById('annotation-layer');
    if (!canvas) return;
    
    // Internal canvas resolution
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    
    const ctx = canvas.getContext('2d');
    
    // Scale coords to match frontend CSS box
    const scaleX = canvas.width / rawVidW;
    const scaleY = canvas.height / rawVidH;
    
    const x = boxCoords[0] * scaleX;
    const y = boxCoords[1] * scaleY;
    const w = boxCoords[2] * scaleX;
    const h = boxCoords[3] * scaleY;
    
    ctx.strokeStyle = '#10B981'; // Emerald
    ctx.lineWidth = 3;
    ctx.setLineDash([8, 4]); // Dashed line for search result
    ctx.strokeRect(x, y, w, h);
    
    // Draw Label bubble
    ctx.fillStyle = '#10B981';
    ctx.fillRect(x, Math.max(0, y - 24), ctx.measureText(label).width + 16, 24);
    
    ctx.fillStyle = '#111827';
    ctx.font = 'bold 12px monospace';
    ctx.fillText(label, x + 8, Math.max(0, y - 24) + 16);
}

// 2. Manual Canvas Drawing Logic
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('annotation-layer');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    let isDrawing = false;
    let startX = 0;
    let startY = 0;
    
    // Ensure resolution
    const resizeCanvas = () => {
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
    };
    
    window.addEventListener('resize', resizeCanvas);
    
    canvas.addEventListener('mousedown', (e) => {
        resizeCanvas(); // Snap res just in case
        isDrawing = true;
        const rect = canvas.getBoundingClientRect();
        startX = e.clientX - rect.left;
        startY = e.clientY - rect.top;
        
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    });

    canvas.addEventListener('mousemove', (e) => {
        if (!isDrawing) return;
        
        const rect = canvas.getBoundingClientRect();
        const currentX = e.clientX - rect.left;
        const currentY = e.clientY - rect.top;
        
        const width = currentX - startX;
        const height = currentY - startY;
        
        // Clear previous frame logic before drawing next preview box
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        ctx.strokeStyle = '#F43F5E'; // Red/Rose for manual draw
        ctx.lineWidth = 2;
        ctx.setLineDash([]); 
        ctx.strokeRect(startX, startY, width, height);
    });

    canvas.addEventListener('mouseup', (e) => {
        if(!isDrawing) return;
        isDrawing = false;
        
        const rect = canvas.getBoundingClientRect();
        const endX = e.clientX - rect.left;
        const endY = e.clientY - rect.top;
        
        const width = endX - startX;
        const height = endY - startY;
        
        if (Math.abs(width) > 10 && Math.abs(height) > 10) {
            logToConsole(`[Manual Annotation] Appended bounding box: [${startX.toFixed(1)}, ${startY.toFixed(1)}, ${width.toFixed(1)}, ${height.toFixed(1)}]`);
            showToast('Manual bounding box locked.', 'success');
            
            const videoPlayer = document.getElementById('video-player');
            const promptInput = document.getElementById('interactive-clip-prompt');
            const videoPath = document.getElementById('annoVideoPath').value;
            
            if (videoPlayer && videoPlayer.src) {
                // Map from canvas sizing back to native video sizing
                const rawVidW = videoPlayer.videoWidth || 1920; 
                const rawVidH = videoPlayer.videoHeight || 1080;
                
                const scaleX = rawVidW / canvas.width;
                const scaleY = rawVidH / canvas.height;
                
                const realX = Math.round(startX * scaleX);
                const realY = Math.round(startY * scaleY);
                const realW = Math.round(width * scaleX);
                const realH = Math.round(height * scaleY);
                
                let label = promptInput.value || "pothole"; // Default label if empty
                const currentTime = videoPlayer.currentTime;
                
                const fs = require('fs');
                const path = require('path');
                const csvPath = path.join(__dirname, '../../manual_annotations.csv');
                
                // Write header if file doesn't exist
                if (!fs.existsSync(csvPath)) {
                    fs.writeFileSync(csvPath, "video,timestamp,x,y,w,h,label,confidence\n");
                }
                
                const row = `${videoPath},${currentTime.toFixed(3)},${realX},${realY},${realW},${realH},${label},1.0\n`;
                fs.appendFileSync(csvPath, row);
                logToConsole(`Saved manual annotation to backend dataset (labels.csv context).`);
                
                // Draw label bubble to confirm it's captured
                ctx.fillStyle = '#F43F5E';
                ctx.fillRect(startX, Math.max(0, startY - 24), ctx.measureText(label).width + 16, 24);
                ctx.fillStyle = '#FFFFFF';
                ctx.font = 'bold 12px monospace';
                ctx.fillText(label, startX + 8, Math.max(0, startY - 24) + 16);
            }
            
        } else {
            ctx.clearRect(0, 0, canvas.width, canvas.height); // Too small, clear it
        }
    });
});


// Auto-Generated Dataset Review Logic
let currentDatasetImages = [];
let currentDatasetIndex = 0;
let isDrawingDataset = false;
let datasetStartX = 0;
let datasetStartY = 0;
let currentBoxes = [];
let selectedBoxIndex = -1;

function setupDatasetGallery() {
    const { ipcRenderer } = require('electron');
    const btnUploadAutoDataset = document.getElementById('btn-upload-auto-dataset');
    const datasetPathLabel = document.getElementById('dataset-path-label');
    const datasetGalleryView = document.getElementById('dataset-gallery-view');
    const datasetPreviewImg = document.getElementById('dataset-preview-img');
    const datasetAnnotationCanvas = document.getElementById('dataset-annotation-canvas');
    const btnDatasetPrev = document.getElementById('btn-dataset-prev');
    const btnDatasetNext = document.getElementById('btn-dataset-next');
    const datasetCounter = document.getElementById('dataset-counter');
    const btnDatasetSave = document.getElementById('btn-dataset-save');
    const btnToolClear = document.getElementById('btn-tool-clear');
    const datasetLabelSelect = document.getElementById('dataset-label-select');
    const datasetColorBox = document.getElementById('dataset-color-box');
    const datasetColorFont = document.getElementById('dataset-color-font');
    const datasetSliderThickness = document.getElementById('dataset-slider-thickness');
    const datasetSliderOpacity = document.getElementById('dataset-slider-opacity');
    const btnDatasetDeleteSelected = document.getElementById('btn-dataset-delete-selected');

    logToConsole('[Dataset Gallery] Init UI check: ' + !!btnUploadAutoDataset + ' ' + !!datasetAnnotationCanvas);
    if (!btnUploadAutoDataset || !datasetAnnotationCanvas) return;

    let datasetContext = datasetAnnotationCanvas.getContext('2d');

    function renderDatasetCanvas(currentX, currentY) {
        datasetContext.clearRect(0, 0, datasetAnnotationCanvas.width, datasetAnnotationCanvas.height);
        
        // Draw saved boxes
        for (let i = 0; i < currentBoxes.length; i++) {
            let box = currentBoxes[i];
            let bColor = box.colorBox || '#F43F5E';
            let fColor = box.colorFont || '#000000';
            let thick = box.thickness || 2;
            
            // Only keeping the stroke perfectly opaque and solid
            datasetContext.globalAlpha = 1.0;

            datasetContext.strokeStyle = i === selectedBoxIndex ? '#00ff00' : bColor;
            datasetContext.fillStyle = i === selectedBoxIndex ? '#00ff00' : bColor;
            datasetContext.lineWidth = i === selectedBoxIndex ? thick + 2 : thick;

            datasetContext.strokeRect(box.x, box.y, box.w, box.h);
            
            // Draw label perfectly opaque
            if (box.label) {
                datasetContext.globalAlpha = 1.0; // Keep font fully readable
                datasetContext.fillStyle = i === selectedBoxIndex ? '#00ff00' : bColor;
                datasetContext.fillRect(box.x, Math.max(0, box.y - 20), datasetContext.measureText(box.label).width + 10, 20);
                datasetContext.fillStyle = fColor;
                datasetContext.font = 'bold 12px monospace';
                datasetContext.fillText(box.label, box.x + 5, Math.max(0, box.y - 20) + 14);
            }
        }

        // Reset alpha for drag box
        datasetContext.globalAlpha = 1.0;

        // Draw current dragging box
        if (isDrawingDataset && currentX !== undefined && currentY !== undefined) {
            let dragThick = datasetSliderThickness ? parseInt(datasetSliderThickness.value) : 2;
            
            datasetContext.globalAlpha = 1.0;
            datasetContext.strokeStyle = '#e0e0e0';
            datasetContext.lineWidth = dragThick;
            datasetContext.strokeRect(datasetStartX, datasetStartY, currentX - datasetStartX, currentY - datasetStartY);
        }
    }

    function loadDatasetImage(index) {
        if (index >= 0 && index < currentDatasetImages.length) {
            datasetPreviewImg.src = "file://" + currentDatasetImages[index];
            datasetCounter.innerText = (index + 1) + " / " + currentDatasetImages.length;
            currentBoxes = [];
            selectedBoxIndex = -1;
            
            if (datasetAnnotationCanvas.width > 0) {
                renderDatasetCanvas();
            }
            // Update label select UI if needed
            if (datasetLabelSelect) datasetLabelSelect.value = "0 - bicycle";
        }
    }

    datasetPreviewImg.onload = () => {
        datasetAnnotationCanvas.width = datasetPreviewImg.clientWidth;
        datasetAnnotationCanvas.height = datasetPreviewImg.clientHeight;
        renderDatasetCanvas();
    };

    btnUploadAutoDataset.addEventListener('click', async () => {
        logToConsole('[Dataset Gallery] Upload button clicked');
        const folderPath = await ipcRenderer.invoke('dialog:openDirectory');
        if (folderPath) {
            datasetPathLabel.innerText = folderPath;
            currentDatasetImages = await ipcRenderer.invoke('read-dir-images', folderPath);
            if (currentDatasetImages && currentDatasetImages.length > 0) {
                currentDatasetIndex = 0;
                datasetGalleryView.classList.remove('hidden');
                loadDatasetImage(currentDatasetIndex);
            } else {
                logToConsole("[WARN] No images found");
            }
        }
    });

    btnDatasetPrev.addEventListener('click', () => {
        if (currentDatasetIndex > 0) {
            currentDatasetIndex--;
            loadDatasetImage(currentDatasetIndex);
        }
    });

    btnDatasetNext.addEventListener('click', () => {
        if (currentDatasetIndex < currentDatasetImages.length - 1) {
            currentDatasetIndex++;
            loadDatasetImage(currentDatasetIndex);
        }
    });

    btnDatasetSave.addEventListener('click', async () => {
        if (currentDatasetImages.length === 0) return;
        selectedBoxIndex = -1; // hide selection before saving
        renderDatasetCanvas();
        
        const offscreen = document.createElement('canvas');
        offscreen.width = datasetPreviewImg.clientWidth;
        offscreen.height = datasetPreviewImg.clientHeight;
        const ctx = offscreen.getContext('2d');
        
        ctx.drawImage(datasetPreviewImg, 0, 0, offscreen.width, offscreen.height);
        ctx.drawImage(datasetAnnotationCanvas, 0, 0);

        const dataUrl = offscreen.toDataURL('image/jpeg', 1.0);
        const success = await ipcRenderer.invoke('save-annotated-image', currentDatasetImages[currentDatasetIndex], dataUrl);
        if (success) {
            logToConsole("[SUCCESS] Saved frame: " + currentDatasetImages[currentDatasetIndex]);
            btnDatasetSave.innerHTML = "SAVED!";
            setTimeout(() => btnDatasetSave.innerHTML = "[SAVE] Overwrite Frame", 1500);
        }
    });

    btnToolClear.addEventListener('click', () => {
        currentBoxes = [];
        selectedBoxIndex = -1;
        renderDatasetCanvas();
    });

    if (datasetLabelSelect) {
        datasetLabelSelect.addEventListener('change', (e) => {
            if (selectedBoxIndex !== -1 && currentBoxes[selectedBoxIndex]) {
                currentBoxes[selectedBoxIndex].label = e.target.value;
                renderDatasetCanvas();
            }
        });
    }

    if (datasetColorBox) {
        datasetColorBox.addEventListener('input', (e) => {
            if (selectedBoxIndex !== -1 && currentBoxes[selectedBoxIndex]) {
                currentBoxes[selectedBoxIndex].colorBox = e.target.value;
                renderDatasetCanvas();
            }
        });
    }

    if (datasetColorFont) {
        datasetColorFont.addEventListener('input', (e) => {
            if (selectedBoxIndex !== -1 && currentBoxes[selectedBoxIndex]) {
                currentBoxes[selectedBoxIndex].colorFont = e.target.value;
                renderDatasetCanvas();
            }
        });
    }

    if (datasetSliderThickness) {
        datasetSliderThickness.addEventListener('input', (e) => {
            if (selectedBoxIndex !== -1 && currentBoxes[selectedBoxIndex]) {
                currentBoxes[selectedBoxIndex].thickness = parseInt(e.target.value);
                renderDatasetCanvas();
            }
        });
    }

    if (datasetSliderOpacity) {
        datasetSliderOpacity.addEventListener('input', (e) => {
            if (selectedBoxIndex !== -1 && currentBoxes[selectedBoxIndex]) {
                currentBoxes[selectedBoxIndex].opacity = parseFloat(e.target.value);
                renderDatasetCanvas();
            }
        });
    }

    if (btnDatasetDeleteSelected) {
        btnDatasetDeleteSelected.addEventListener('click', () => {
            if (selectedBoxIndex !== -1 && currentBoxes[selectedBoxIndex]) {
                currentBoxes.splice(selectedBoxIndex, 1);
                selectedBoxIndex = -1;
                renderDatasetCanvas();
            }
        });
    }

    datasetAnnotationCanvas.addEventListener('mousedown', (e) => {
        const rect = datasetAnnotationCanvas.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const clickY = e.clientY - rect.top;

        // Check if we clicked an existing box (from top to bottom / newest to oldest visually)
        let clickedExistingBox = false;
        for (let i = currentBoxes.length - 1; i >= 0; i--) {
            const box = currentBoxes[i];
            const left = Math.min(box.x, box.x + box.w);
            const right = Math.max(box.x, box.x + box.w);
            const top = Math.min(box.y, box.y + box.h);
            const bottom = Math.max(box.y, box.y + box.h);

            if (clickX >= left && clickX <= right && clickY >= top && clickY <= bottom) {
                selectedBoxIndex = i;
                clickedExistingBox = true;
                if (datasetLabelSelect) {
                    datasetLabelSelect.value = box.label || "0 - bicycle";
                }
                if (datasetColorBox) {
                    datasetColorBox.value = box.colorBox || "#F43F5E";
                }
                if (datasetColorFont) {
                    datasetColorFont.value = box.colorFont || "#000000";
                }
                if (datasetSliderThickness) {
                    datasetSliderThickness.value = box.thickness || 2;
                }
                if (datasetSliderOpacity) {
                    let dispOpac = box.opacity !== undefined ? box.opacity : 100;
                    if (dispOpac <= 1.0 && dispOpac > 0) dispOpac *= 100;
                    datasetSliderOpacity.value = dispOpac;
                }
                break;
            }
        }

        if (clickedExistingBox) {
            isDrawingDataset = false;
            renderDatasetCanvas();
        } else {
            isDrawingDataset = true;
            selectedBoxIndex = -1;
            datasetStartX = clickX;
            datasetStartY = clickY;
            renderDatasetCanvas();
        }
    });

    datasetAnnotationCanvas.addEventListener('mousemove', (e) => {
        if (!isDrawingDataset) return;
        const rect = datasetAnnotationCanvas.getBoundingClientRect();
        const currentX = e.clientX - rect.left;
        const currentY = e.clientY - rect.top;
        renderDatasetCanvas(currentX, currentY);
    });

    datasetAnnotationCanvas.addEventListener('mouseup', (e) => {
        if (!isDrawingDataset) return;
        isDrawingDataset = false;
        
        const rect = datasetAnnotationCanvas.getBoundingClientRect();
        const currentX = e.clientX - rect.left;
        const currentY = e.clientY - rect.top;

        const w = currentX - datasetStartX;
        const h = currentY - datasetStartY;

        // Only add if it's large enough
        if (Math.abs(w) > 5 && Math.abs(h) > 5) {
            let initialLabel = "0 - bicycle";
            let cBox = "#F43F5E";
            let cFont = "#000000";
            let thick = 2;
            let opac = 100;

            if (datasetLabelSelect) initialLabel = datasetLabelSelect.value;
            if (datasetColorBox) cBox = datasetColorBox.value;
            if (datasetColorFont) cFont = datasetColorFont.value;
            if (datasetSliderThickness) thick = parseInt(datasetSliderThickness.value);
            if (datasetSliderOpacity) opac = parseFloat(datasetSliderOpacity.value);
            
            const newBox = {
                x: datasetStartX,
                y: datasetStartY,
                w: w,
                h: h,
                label: initialLabel,
                colorBox: cBox,
                colorFont: cFont,
                thickness: thick,
                opacity: opac
            };
            currentBoxes.push(newBox);
            selectedBoxIndex = currentBoxes.length - 1; // auto select new box
            if (datasetLabelSelect) datasetLabelSelect.value = initialLabel;
        }
        
        renderDatasetCanvas();
    });
}

function setupClipClasses() {
    const labelsPath = path.join(rootDir, 'config/labels.json');
    if (!fs.existsSync(labelsPath)) return;
    
    let labelsData;
    try {
        labelsData = JSON.parse(fs.readFileSync(labelsPath, 'utf8'));
    } catch(e) {
        console.error('Error parsing labels.json', e);
        return;
    }
    const targetClasses = Object.keys(labelsData);
    const clipContainer = document.getElementById('clip-classes-container');
    const selectAllBtn = document.getElementById('btn-select-all');
    const datasetLabelSelect = document.getElementById('dataset-label-select');

    // Populate drop down for manual manual annotations label select
    if (datasetLabelSelect) {
        datasetLabelSelect.innerHTML = '';
        targetClasses.forEach(cls => {
            const opt = document.createElement('option');
            opt.value = cls;
            opt.innerText = cls;
            datasetLabelSelect.appendChild(opt);
        });
    }

    if (clipContainer) {
        clipContainer.innerHTML = '';
        targetClasses.forEach(cls => {
            const wrapper = document.createElement('div');
            wrapper.className = 'flex items-center gap-2';
            wrapper.innerHTML = `
                <input type="checkbox" id="clip-cls-${cls}" value="${cls}" checked class="checkbox checkbox-xs checkbox-primary clip-class-checkbox" />
                <label for="clip-cls-${cls}" class="text-xs truncate text-[#e0e0e0] cursor-pointer" title="${cls}">${cls}</label>
            `;
            clipContainer.appendChild(wrapper);
        });

        if (selectAllBtn) {
            selectAllBtn.checked = true;
            selectAllBtn.addEventListener('change', (e) => {
                document.querySelectorAll('.clip-class-checkbox').forEach(cb => {
                    cb.checked = e.target.checked;
                });
            });
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    setupDatasetGallery();
    setupClipClasses();
});

if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setupDatasetGallery();
    setupClipClasses();
}

// ==== NEW LOGIC FOR MANUAL CAPTURE & ANNOTATION TOGGLE ====
let manualCaptureFolder = '';
let isManualAnnotationOn = false;

document.addEventListener('DOMContentLoaded', () => {
    const btnToggle = document.getElementById('btn-toggle-annotation');
    const btnSetFolder = document.getElementById('btn-set-capture-folder');
    const btnCapture = document.getElementById('btn-capture-frame');
    const annotationLayer = document.getElementById('annotation-layer');
    const videoPlayer = document.getElementById('video-player');

    if (btnToggle) {
        btnToggle.addEventListener('click', () => {
            isManualAnnotationOn = !isManualAnnotationOn;
            if (isManualAnnotationOn) {
                btnToggle.innerText = "Annotation: ON";
                btnToggle.classList.replace('text-[#e0e0e0]', 'text-emerald-400');
                annotationLayer.classList.remove('pointer-events-none');
                annotationLayer.classList.add('pointer-events-auto');
            } else {
                btnToggle.innerText = "Annotation: OFF";
                btnToggle.classList.replace('text-emerald-400', 'text-[#e0e0e0]');
                annotationLayer.classList.remove('pointer-events-auto');
                annotationLayer.classList.add('pointer-events-none');
            }
        });
    }

    if (btnSetFolder) {
        btnSetFolder.addEventListener('click', async () => {
            const { ipcRenderer } = require('electron');
            const path = await ipcRenderer.invoke('dialog:openDirectory');
            if (path) {
                manualCaptureFolder = path;
                showToast("Capture folder set to: " + path, "success");
            }
        });
    }

    if (btnCapture) {
        btnCapture.addEventListener('click', async () => {
            if (!videoPlayer || !videoPlayer.src) {
                showToast("No video loaded to capture", "error");
                return;
            }
            if (!manualCaptureFolder) {
                showToast("Please Set Output Folder first", "error");
                return;
            }

            const rawVidW = videoPlayer.videoWidth;
            const rawVidH = videoPlayer.videoHeight;
            if (!rawVidW || !rawVidH) return;

            // Draw frame to hidden canvas
            const hiddenCanvas = document.createElement('canvas');
            hiddenCanvas.width = rawVidW;
            hiddenCanvas.height = rawVidH;
            const hCtx = hiddenCanvas.getContext('2d');
            
            // Draw video frame
            hCtx.drawImage(videoPlayer, 0, 0, rawVidW, rawVidH);

            // Draw annotations on top
            hCtx.drawImage(annotationLayer, 0, 0, rawVidW, rawVidH);

            // Export to PNG base64
            const dataUrl = hiddenCanvas.toDataURL('image/png');
            
            // Generate filename based on current video time and timestamp
            const timestamp = new Date().toISOString().replace(/[:.-]/g, '_');
            const path = require('path');
            const savePath = path.join(manualCaptureFolder, "capture_" + timestamp + ".png");

            const { ipcRenderer } = require('electron');
            const success = await ipcRenderer.invoke('save-annotated-image', savePath, dataUrl);
            if (success) {
                showToast("Frame captured successfully to " + savePath, "success");
            } else {
                showToast("Failed to save frame", "error");
            }
        });
    }
});


function initLossChart() {
  const ctx = document.getElementById('lossChart');
  if (!ctx) return;
  
  if (lossChartInstance) {
    lossChartInstance.destroy();
  }
  
  const Chart = window.Chart; // Assuming added to window via html tag
  if (!Chart) { appendLog('Note: Chart.js not loaded. Live graphs disabled.'); return; }

  lossChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        { label: 'Train Loss', data: [], borderColor: 'rgb(244, 63, 94)', backgroundColor: 'rgba(244, 63, 94, 0.1)', tension: 0.3, pointRadius: 2, fill: false },
        { label: 'Val Loss', data: [], borderColor: 'rgb(59, 130, 246)', backgroundColor: 'rgba(59, 130, 246, 0.1)', tension: 0.3, pointRadius: 3, borderDash: [5, 5], fill: true }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: true, labels: { color: '#888' } } },
      scales: {
        x: { grid: { color: '#222' }, ticks: { color: '#888', maxTicksLimit: 10 } },
        y: { grid: { color: '#222' }, ticks: { color: '#888' } }
      },
      animation: { duration: 300 }
    }
  });
}


window.initLossChart = function() {
  const ctx = document.getElementById('lossChart');
  if (!ctx) return;
  
  if (window.lossChartInstance) {
    window.lossChartInstance.destroy();
  }
  
  if (typeof Chart === 'undefined') { console.log('Chart.js not loaded'); return; }

  window.lossChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        { label: 'Train Loss', data: [], borderColor: 'rgb(244, 63, 94)', backgroundColor: 'rgba(244, 63, 94, 0.1)', tension: 0.3, pointRadius: 2, fill: false },
        { label: 'Val Loss', data: [], borderColor: 'rgb(59, 130, 246)', backgroundColor: 'rgba(59, 130, 246, 0.1)', tension: 0.3, pointRadius: 3, borderDash: [5, 5], fill: true }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: true, labels: { color: '#888' } } },
      scales: {
        x: { grid: { color: '#222' }, ticks: { color: '#888', maxTicksLimit: 10 } },
        y: { grid: { color: '#222' }, ticks: { color: '#888' } }
      },
      animation: { duration: 300 }
    }
  });
}

function stopActiveProcess() {
    if (window.activeTrainingProcess) {
        window.activeTrainingProcess.kill();
        logToConsole(`
[System] Process violently terminated.
`);
    }
}

window.stopClipProcess = function() {
    if (window.activeClipProcess) {
        window.activeClipProcess.kill();
        logToConsole(`\n[System] Auto Annotation aborted safely.\n`);
    }
}

window.chooseResumeModel = async function() {
  const file = await ipcRenderer.invoke('dialog:openModel');
  if (file) {
    document.getElementById('trainResumePath').value = file;
  }
};
