
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
  'dino': path.join(rootDir, 'data_pipeline/grounding_dino_auto.py'),
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

window.switchView = function(viewName) {
  require('fs').appendFileSync('/tmp/clicked.log', 'Clicked: ' + viewName + '\n');
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
  if (message.match(/Epoch/i) || message.match(/Loss/i) || message.match(/\[\d+\/\d+\]/)) {
    document.getElementById('training-stats').classList.remove('hidden');
    
    // Parse formats like "[1/50]", "Epoch [1/50]", "Epoch 1/50"
    const epochMatch = message.match(/(?:Epoch\s*\[?)?(\d+)\s*\/\s*(\d+)/i);
    // Parse formats like "Epoch 1 Summary"
    const epochSummaryMatch = message.match(/Epoch (\d+) Summary/i);

    const trainLossMatch = message.match(/Train Loss:\s*([0-9.]+)/i);
    const valLossMatch = message.match(/(?:Val|Validation) Loss:\s*([0-9.]+)/i);
    const valAccMatch = message.match(/(?:Val|Validation) Acc:\s*([0-9.]+)/i);

    let currentEpochStr = null;

    if (epochMatch) {
      document.getElementById('stat-epoch').innerText = epochMatch[1];
      const elTotal = document.getElementById('stat-epoch-total');
      if (elTotal) elTotal.innerText = epochMatch[2];
      
      const current = parseInt(epochMatch[1]);
      const total = parseInt(epochMatch[2]);
      currentEpochStr = epochMatch[1];
      const progressPercent = (current / total) * 100;
      const progEl = document.getElementById('stat-progress');
      if (progEl) progEl.value = progressPercent;
    } else if (epochSummaryMatch) {
      document.getElementById('stat-epoch').innerText = epochSummaryMatch[1];
      currentEpochStr = epochSummaryMatch[1];
    }
    
    if (valLossMatch) {
        document.getElementById('stat-loss').innerText = valLossMatch[1];
    }
    
    if (valAccMatch) {
        document.getElementById('stat-accuracy').innerText = valAccMatch[1] + "%";
    }
    
    // Update live Chart.js Graph
    if ((trainLossMatch || valLossMatch) && window.lossChartInstance && currentEpochStr !== null) {
        const cLabels = window.lossChartInstance.data.labels;
        const cTrain = window.lossChartInstance.data.datasets[0].data;
        const cVal = window.lossChartInstance.data.datasets[1].data;
        
        const epochIndex = cLabels.indexOf(currentEpochStr);
        
        if (epochIndex !== -1) {
            // Update existing if already pushed this epoch
            if (trainLossMatch) cTrain[epochIndex] = parseFloat(trainLossMatch[1]);
            if (valLossMatch) cVal[epochIndex] = parseFloat(valLossMatch[1]);
        } else {
            // Append new epoch point
            cLabels.push(currentEpochStr);
            cTrain.push(trainLossMatch ? parseFloat(trainLossMatch[1]) : null);
            cVal.push(valLossMatch ? parseFloat(valLossMatch[1]) : null);
        }
        window.lossChartInstance.update();
    }
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

window.chooseSyncDir = async () => {
  const { ipcRenderer } = require('electron');
  const dir = await ipcRenderer.invoke('dialog:openDirectory');
  if (dir) {
    document.getElementById('syncDataPath').value = dir;
  }
};

window.chooseSyncOut = async () => {
  const { ipcRenderer } = require('electron');
  const dir = await ipcRenderer.invoke('dialog:openDirectory');
  if (dir) {
    document.getElementById('syncCustomOutPath').value = dir;
  }
};

window.chooseTrainOut = async () => {
  const { ipcRenderer } = require('electron');
  const dir = await ipcRenderer.invoke('dialog:openDirectory');
  if (dir) {
    document.getElementById('trainCustomOutPath').value = dir;
  }
};

window.chooseAdhocImu = async () => {
    const { ipcRenderer } = require('electron');
    const file = await ipcRenderer.invoke('dialog:openCSV');
    if (file) {
      document.getElementById('adhocImuPath').value = file;
    }
};

window.chooseAdhocLabel = async () => {
    const { ipcRenderer } = require('electron');
    const file = await ipcRenderer.invoke('dialog:openCSV');
    if (file) {
      document.getElementById('adhocLabelPath').value = file;
    }
};

window.syncSyncPaths = () => {
    const frames = document.getElementById('syncFramesPath').value;
    const annoDir = document.getElementById('annoDirPath');
    if (annoDir && !annoDir.value) {
        annoDir.value = frames;
        setDirectory();
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
  if (scriptKey === 'clip' || scriptKey === 'dino') {
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

     const maxFramesEl = document.getElementById('clipMaxFrames');
     if (maxFramesEl && maxFramesEl.value) {
         args.push('--max_frames', maxFramesEl.value);
     }
     
     const saveFramesEl = document.getElementById('clipSaveFrames');
     if (saveFramesEl && !saveFramesEl.checked) {
         args.push('--no_save_frames');
     }

     const selectedClasses = [];
     document.querySelectorAll('.clip-class-checkbox:checked').forEach(cb => {
         selectedClasses.push(cb.value);
     });
     if (selectedClasses.length > 0) {
         args.push('--classes', ...selectedClasses);
     }
     
     if (scriptKey === 'clip') {
         const modelSelectEl = document.getElementById('clipModelSelect');
         if (modelSelectEl && modelSelectEl.value) {
             args.push('--model', modelSelectEl.value);
         }
         const confSliderEl = document.getElementById('clipConfSlider');
         if (confSliderEl && confSliderEl.value) {
             args.push('--conf', (parseFloat(confSliderEl.value) / 100).toFixed(2));
         }
     } else if (scriptKey === 'dino') {
         args.push('--conf', '0.25'); 
         args.push('--text_conf', '0.25');
     }
  }
  if (scriptKey === 'extract') {
    const extractVideoPathValue = document.getElementById('extractVideoPath') ? document.getElementById('extractVideoPath').value.trim() : "";
      const customOutPath = document.getElementById('extractCustomOutPath') ? document.getElementById('extractCustomOutPath').value.trim() : "";
      const startTimeEl = document.getElementById('extractStartTime');
      const startTimeOverride = startTimeEl ? startTimeEl.value : "";
      const fpsSelectEl = document.getElementById('extractFpsSelect');
      const fpsValue = fpsSelectEl ? fpsSelectEl.value : "10";
      
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
    args.push('--fps', fpsValue);

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
          const frames = document.getElementById('syncFramesPath') ? document.getElementById('syncFramesPath').value.trim() : "";

          if (!imu || !label) {
              logToConsole("[WARN] Ad-Hoc sync requires both IMU and Label CSVs.\n", true);
              return;
          }
          args.push('--imu_csv', imu);
          args.push('--label_csv', label);
          if (frames) args.push('--frames_dir', frames);
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

      // Custom Output Directory
      const syncOut = document.getElementById('syncCustomOutPath') ? document.getElementById('syncCustomOutPath').value.trim() : "";
      if (syncOut) args.push('--output_dir', syncOut);
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
        const trainOut = document.getElementById('trainCustomOutPath') ? document.getElementById('trainCustomOutPath').value.trim() : "";

        if (useVision) args.push('--use_vision');
        if (useImu) args.push('--use_imu');
        
        if (epochs) args.push('--epochs', epochs);
        if (lr) args.push('--lr', lr);
        if (batch) args.push('--batch_size', batch);
        if (checkpoint) args.push('--checkpoint', checkpoint);
        if (trainOut) args.push('--output_dir', trainOut);

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

window.chooseInfLabel = async function() {
  const { ipcRenderer } = require('electron');
  const file = await ipcRenderer.invoke('dialog:openCSV');
  if (file) {
    document.getElementById('infLabelPath').value = file;
  }
};

window.convertTimeToUnix = function() {
    const input = document.getElementById('extractStartTime');
    if (!input || !input.value.trim()) return;
    
    const val = input.value.trim();
    // If it's already a number, don't do anything
    if (!isNaN(val)) {
        showToast("Already a Unix timestamp.", "info");
        return;
    }
    
    try {
        // Try parsing common formats like "2024-06-17, 10:51:27.2810"
        let cleanVal = val.replace(',', ''); // remove comma if present
        const date = new Date(cleanVal);
        if (isNaN(date.getTime())) {
            throw new Error("Invalid Format");
        }
        const unix = (date.getTime() / 1000).toFixed(3);
        input.value = unix;
        showToast(`Converted to: ${unix}`, "success");
    } catch (e) {
        showToast("Error: Use format YYYY-MM-DD HH:MM:SS", "error");
    }
};

let liveImuChart = null;
let liveRadarChart = null;
let spectrogramCtx = null;
let vectorBallCtx = null;
let spectrogramData = Array.from({length: 80}, () => Array(25).fill(0));
let mapMarker = null;

window.initLiveDashboard = function() {
    // 1. Live IMU Scrubbing
    const imuCanvas = document.getElementById('inf-imu-chart');
    if (imuCanvas && !liveImuChart) {
        // We defer to window.Chart (it should be loaded in HTML)
        liveImuChart = new Chart(imuCanvas, {
            type: 'line',
            data: {
                labels: Array(50).fill(''),
                datasets: [
                    { label: 'Accel X', data: Array(50).fill(0), borderColor: '#10b981', borderWidth: 1, tension: 0.1, pointRadius: 0 },
                    { label: 'Accel Y', data: Array(50).fill(0), borderColor: '#3b82f6', borderWidth: 1, tension: 0.1, pointRadius: 0 },
                    { label: 'Accel Z', data: Array(50).fill(0), borderColor: '#f43f5e', borderWidth: 1, tension: 0.1, pointRadius: 0 }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false, animation: false, scales: { x: { display: false }, y: { display: true, min: -20, max: 20 } }, plugins: { legend: { display: false } } }
        });
    }

    // 2. Radar Chart
    const radarCanvas = document.getElementById('inf-radar-chart');
    if (radarCanvas && !liveRadarChart) {
        liveRadarChart = new Chart(radarCanvas, {
            type: 'radar',
            data: {
                labels: ['Asphalt', 'Gravel', 'Cobblestone', 'Grass', 'Pothole', 'SpeedBump', 'Braking', 'Turning', 'Wet', 'Sand'],
                datasets: [{
                    label: 'Confidence',
                    data: Array(10).fill(10),
                    backgroundColor: 'rgba(168, 85, 247, 0.2)',
                    borderColor: '#a855f7',
                    pointBackgroundColor: '#a855f7',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#a855f7'
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false, animation: { duration: 150 },
                scales: { r: { min: 0, max: 100, ticks: { display: false }, grid: { color: '#333' }, angleLines: { color: '#333' }, pointLabels: { color: '#888', font: { size: 9 } } } },
                plugins: { legend: { display: false } }
            }
        });
    }

    // 3. FFT Spectrogram Setup
    const specCanvas = document.getElementById('inf-spectrogram-canvas');
    if (specCanvas) {
        specCanvas.width = specCanvas.offsetWidth || 400;
        specCanvas.height = specCanvas.offsetHeight || 150;
        spectrogramCtx = specCanvas.getContext('2d');
    }

    // 4. Vector Ball Setup
    const vectorCanvas = document.getElementById('inf-vector-ball-canvas');
    if (vectorCanvas) {
        vectorCanvas.width = vectorCanvas.offsetWidth || 200;
        vectorCanvas.height = vectorCanvas.offsetHeight || 128;
        vectorBallCtx = vectorCanvas.getContext('2d');
    }
}

window.updateLiveDashboard = function(pred, time) {
    if (!pred) return;
    
    let variance = pred.variance_metric || 0.5;
    let mainSurface = pred.surface || "";
    let conf = pred.confidence || 100;

    // 1. Update IMU Chart (simulate noisy sine waves scaled by variance)
    if (liveImuChart) {
        liveImuChart.data.datasets.forEach((dataset, idx) => {
            dataset.data.shift(); // remove first
            let noise = (Math.random() - 0.5) * variance * (idx + 2) * 5;
            let val = Math.sin(time * 10 + idx) * (variance) + noise;
            val = Math.max(-20, Math.min(20, val));
            dataset.data.push(val);
        });
        liveImuChart.update();
    }

    // 2. Update Radar (spike the correct class)
    if (liveRadarChart) {
        const labels = liveRadarChart.data.labels;
        let newData = labels.map((l) => {
            if (mainSurface.includes(l) || l.includes(mainSurface.split(' ')[0])) {
                return conf;
            }
            return Math.random() * 20; // Background noise probabilities
        });
        liveRadarChart.data.datasets[0].data = newData;
        liveRadarChart.update();
    }

    // 3. Update Spectrogram Waterfall
    if (spectrogramCtx) {
        const w = spectrogramCtx.canvas.width;
        const h = spectrogramCtx.canvas.height;
        spectrogramData.shift();
        let newCol = Array(25).fill(0).map((_, i) => Math.random() * variance * (25 - i) / 5);
        spectrogramData.push(newCol);
        
        spectrogramCtx.clearRect(0, 0, w, h);
        const colW = w / 80;
        const rowH = h / 25;
        for (let x = 0; x < 80; x++) {
            for (let y = 0; y < 25; y++) {
                let val = spectrogramData[x][y];
                // Jet colormap logic
                let r = Math.min(255, val * 10);
                let g = Math.min(255, val * 30);
                let b = Math.max(0, 255 - val * 10);
                spectrogramCtx.fillStyle = `rgb(${r},${g},${b})`;
                spectrogramCtx.fillRect(x * colW, h - (y * rowH) - rowH, colW+1, rowH+1); // +1 fixes gaps
            }
        }
    }

    // 4. Update Vector Ball
    if (vectorBallCtx) {
        const w = vectorBallCtx.canvas.width;
        const h = vectorBallCtx.canvas.height;
        const cx = w / 2; const cy = h / 2;
        vectorBallCtx.clearRect(0, 0, w, h);
        
        // Radar Crosshairs
        vectorBallCtx.strokeStyle = '#333';
        vectorBallCtx.beginPath();
        vectorBallCtx.moveTo(cx, 0); vectorBallCtx.lineTo(cx, h);
        vectorBallCtx.moveTo(0, cy); vectorBallCtx.lineTo(w, cy);
        vectorBallCtx.stroke();
        vectorBallCtx.beginPath(); vectorBallCtx.arc(cx, cy, h/3, 0, 2*Math.PI); vectorBallCtx.stroke();

        let dx = (Math.random() - 0.5) * variance * 15;
        let dy = (Math.random() - 0.5) * variance * 15;
        
        vectorBallCtx.beginPath();
        vectorBallCtx.arc(cx + dx, cy + dy, 8, 0, 2 * Math.PI);
        vectorBallCtx.fillStyle = '#f43f5e';
        vectorBallCtx.shadowBlur = 10; vectorBallCtx.shadowColor = '#f43f5e';
        vectorBallCtx.fill(); 
        vectorBallCtx.shadowBlur = 0;
    }

    // 5. Update Severity Spike ProgressBar
    const sevBar = document.getElementById('inf-severity-bar');
    if (sevBar) {
        let pct = Math.min(100, (variance / 8.0) * 100);
        sevBar.style.width = pct + '%';
        sevBar.style.backgroundColor = pct > 60 ? '#ef4444' : (pct > 30 ? '#f59e0b' : '#10b981');
    }
    
    // 6. Update Map Marker
    if (typeof infMap !== 'undefined' && infMap && window.infLatlngs) {
        if (!mapMarker && window.infLatlngs.length > 0) {
            mapMarker = L.circleMarker(window.infLatlngs[0], {color: '#000', fillColor: '#3b82f6', fillOpacity: 1, radius: 6, weight: 2}).addTo(infMap);
        }
        if (mapMarker) {
            const vid = document.getElementById('inf-video');
            if (vid && vid.duration) {
                let progress = time / vid.duration;
                let idx = Math.floor(progress * (window.infLatlngs.length - 1));
                idx = Math.max(0, Math.min(window.infLatlngs.length - 1, idx));
                mapMarker.setLatLng(window.infLatlngs[idx]);
                infMap.panTo(window.infLatlngs[idx], {animate: true, duration: 0.1});
            }
        }
    }
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
            for(let i=0; i<150; i++) {
                latlngs.push([curl, curlg]);
                // Smoother route pathing
                curl += (Math.sin(i*0.1) - 0.5) * 0.0005;
                curlg += (Math.cos(i*0.2) + 0.5) * 0.0005;
            }
            window.infLatlngs = latlngs;
            L.polyline(latlngs, {color: '#94a3b8', weight: 4, dashArray: '4, 6'}).addTo(infMap);
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
    
    // Reveal Monitoring Dashboard
    const dashboard = document.getElementById('inf-monitoring-dashboard');
    if(dashboard) {
        dashboard.classList.remove('hidden');
        setTimeout(window.initLiveDashboard, 300); // Give CSS max bounds time to apply before initing charts
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
               window.updateLiveDashboard(currentPred, currentTime);
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
let confChart = null, classBarChart = null, convergenceChart = null, stabilityChart = null, distributionChart = null;
let scrubberInterval = null;

let analyticsMap = null;
let geoLayerGroup = null;
const { OpenLocationCode } = require('open-location-code');
const olcInstance = new OpenLocationCode();

function initAnalytics() {
    // Removed confChart initialization

    // 2. Per-Class Accuracy
    const ctxClassBar = document.getElementById('class-bar-canvas');
    // Removed classBarChart initialization

    // Removed convergenceChart initialization

    // 4. Temporal Stability (Flicker)
    // Removed stabilityChart initialization

    // 6. Geospatial Map
    const mapDiv = document.getElementById('analytics-map');
    if (mapDiv && !analyticsMap && typeof L !== 'undefined') {
        analyticsMap = L.map('analytics-map', {
            zoomControl: false,
            attributionControl: false
        }).setView([52.5200, 13.4050], 13);
        
        // Use a dark-themed tile layer 
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            maxZoom: 19
        }).addTo(analyticsMap);

        geoLayerGroup = L.layerGroup().addTo(analyticsMap);

        // No mock data generated here. Waiting for CSV/Scraper load.
        window.classState = {};
// Force Leaflet to recalculate its CSS rendering area since it gets 
        // instantiated inside a hidden tab and will layout incorrectly.
        setTimeout(() => {
            analyticsMap.invalidateSize();
        }, 300);
    } else if (analyticsMap) {
        setTimeout(() => analyticsMap.invalidateSize(), 300);
    }
}

// Ensure it initializes when switching tabs
const oldSwitchView = window.switchView || function(){};
window.switchView = function(viewId) {
    oldSwitchView(viewId);
    if(viewId === 'analytics') {
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

window.currentGeoData = [];

window.scrapeGeospatialFolder = async function() {
    const { ipcRenderer } = require('electron');
    const { opendirSync, statSync, readFileSync } = require('fs');
    const { join } = require('path');
    
    const folderPath = await ipcRenderer.invoke('dialog:openDirectory');
    if (!folderPath) return;

    window.currentGeoData = [];
    if (geoLayerGroup) {
        analyticsMap.removeLayer(geoLayerGroup);
    }
    geoLayerGroup = L.layerGroup().addTo(analyticsMap);

    // Provide a status update to the user
    const statsText = document.getElementById('geo-stats-text');
    if (statsText) statsText.innerText = `Scraping GNSS files...`;

    let totalPoints = 0;
    
    // Recursive folder scan
    function scanDirectory(dir) {
        try {
            const dirEntries = require('fs').readdirSync(dir, { withFileTypes: true });
            
            for (const dirent of dirEntries) {
                const res = require('path').join(dir, dirent.name);
                if (dirent.isDirectory()) {
                    scanDirectory(res);
                } else if (dirent.isFile() && dirent.name.toLowerCase().endsWith('.csv') && (res.toLowerCase().includes('gnss') || res.toLowerCase().includes('aligned') || res.toLowerCase().includes('label'))) {
                    // It's a GNSS CSV file, read it
                    processCSV(res);
                }
            }
        } catch (e) {
            console.error('Error scanning folder:', e);
        }
    }
    
    function processCSV(filePath) {
        try {
            const data = require('fs').readFileSync(filePath, 'utf-8');
            const lines = data.trim().split('\n');
            if (lines.length < 2) return;
            
            const parseCSVLine = (line) => {
                const cols = [];
                let inside = false;
                let current = '';
                for (let i = 0; i < line.length; i++) {
                    const char = line[i];
                    if (char === '"') {
                        inside = !inside;
                    } else if (char === ',' && !inside) {
                        cols.push(current.trim().replace(/^"|"$/g, ''));
                        current = '';
                    } else {
                        current += char;
                    }
                }
                cols.push(current.trim().replace(/^"|"$/g, ''));
                return cols;
            };
            
            let headers = parseCSVLine(lines[0]).map(h => h.toLowerCase());
            let latIdx = headers.findIndex(h => h.includes('lat'));
            let lonIdx = headers.findIndex(h => h.includes('lon') || h.includes('lng'));
            let classIdx = headers.findIndex(h => h.includes('class') || h.includes('surface') || h.includes('type') || h.includes('label') || h.includes('pred') || h.includes('vocab'));
            
            if (latIdx === -1 || lonIdx === -1) return;
            
            const olcLocalInstance = new OpenLocationCode();
            
            for (let i = 1; i < lines.length; i++) {
                if (!lines[i].trim()) continue;
                const cols = parseCSVLine(lines[i]);
                if (cols.length <= Math.max(latIdx, lonIdx)) continue;
                
                const lat = parseFloat(cols[latIdx]);
                const lon = parseFloat(cols[lonIdx]);
                
                // Avoid zeroes and invalid numbers created from bad parses
                if (isNaN(lat) || isNaN(lon) || lat === 0 || lon === 0) continue;
                
                // If it doesn't exist, log as Unknown
                let surfaceType = classIdx !== -1 && cols[classIdx] ? cols[classIdx].trim() : 'Unclassified'; if (!surfaceType || surfaceType==='Unknown') surfaceType = 'Unclassified';
                
                let plusCode = 'N/A';
                try {
                    plusCode = olcLocalInstance.encode(lat, lon);
                } catch(e) {}
                
                window.currentGeoData.push({
                    lat: lat,
                    lon: lon,
                    surface: surfaceType, // Match the key used in exporting
                    plusCode: plusCode
                });
                
                window.registerSurface(surfaceType);
                totalPoints++;
            }
        } catch (e) {
            console.error('Error reading CSV:', filePath, e);
        }
    }

    // Ensure map is initialized
    if (!analyticsMap) initAnalytics();

    scanDirectory(folderPath);

    if (window.currentGeoData.length > 0) {
        // Fit map bounds to the markers
        const bounds = L.latLngBounds(window.currentGeoData.map(d => [d.lat, d.lon]));
        analyticsMap.fitBounds(bounds, { padding: [50, 50] });
        window.renderLegend();
        window.updateMapState();
    }
    
    if (statsText) {
        statsText.innerText = `Scraped ${totalPoints} GPS points.`;
    }
}

window.loadGeospatialCSV = async function() {
    const { ipcRenderer } = require('electron');
    const filePath = await ipcRenderer.invoke('dialog:openCSV');
    if (!filePath) return;
    
    try {
        const data = require('fs').readFileSync(filePath, 'utf-8');
        const lines = data.trim().split('\n');
        if (lines.length < 2) return;
        
        const parseCSVLine = (line) => {
            const cols = [];
            let inside = false;
            let current = '';
            for (let i = 0; i < line.length; i++) {
                const char = line[i];
                if (char === '"') {
                    inside = !inside;
                } else if (char === ',' && !inside) {
                    cols.push(current.trim().replace(/^"|"$/g, ''));
                    current = '';
                } else {
                    current += char;
                }
            }
            cols.push(current.trim().replace(/^"|"$/g, ''));
            return cols;
        };
        
        let headers = parseCSVLine(lines[0]).map(h => h.toLowerCase());
        let latIdx = headers.findIndex(h => h.includes('lat'));
        let lonIdx = headers.findIndex(h => h.includes('lon') || h.includes('lng'));
        let classIdx = headers.findIndex(h => h.includes('class') || h.includes('surface') || h.includes('type') || h.includes('label') || h.includes('pred') || h.includes('vocab'));
        
        if (latIdx === -1 || lonIdx === -1) {
            showToast('GPS coordinates missing! Please upload aligned_dataset.csv, not purely labels.', 'error');
            return;
        }

        // Ensure map is initialized
        if (!analyticsMap) initAnalytics();
        
        if (geoLayerGroup) {
            analyticsMap.removeLayer(geoLayerGroup);
        }
        geoLayerGroup = L.featureGroup().addTo(analyticsMap);
        
        const bounds = [];
        window.currentGeoData = [];
        
        for (let i = 1; i < lines.length; i++) {
            if (!lines[i].trim()) continue;
            let row = parseCSVLine(lines[i]);
            if (row.length < 3) continue;
            
            let lat = parseFloat(row[latIdx !== -1 ? latIdx : 0]);
            let lon = parseFloat(row[lonIdx !== -1 ? lonIdx : 1]);
            let surface = classIdx !== -1 && row[classIdx] ? row[classIdx].trim() : 'Unclassified'; if (!surface || surface==='Unknown') surface = 'Unclassified';
            
            if (isNaN(lat) || isNaN(lon) || lat === 0 || lon === 0) continue;
            
            bounds.push([lat, lon]);
            
            let plusCode = 'N/A';
            try {
                plusCode = typeof olcInstance !== 'undefined' ? olcInstance.encode(lat, lon) : 'N/A';
            } catch(e) {}
            
            window.currentGeoData.push({lat, lon, surface, plusCode});
            window.registerSurface(surface);
        }
        
        if (bounds.length > 0) {
            analyticsMap.fitBounds(bounds, { padding: [20, 20] });
            document.getElementById('geo-stats-text').innerText = `Loaded ${bounds.length} waypoints via +Codes`;
            window.renderLegend();
            window.updateMapState();
        }
        
    } catch (err) {
        showToast('Error reading GPS CSV: ' + err.message, 'error');
    }
};

window.exportGeospatialCSV = async function() {
    const { ipcRenderer } = require('electron');
    if (!window.currentGeoData || window.currentGeoData.length === 0) {
        showToast('No geospatial data to export!', 'error');
        return;
    }
    
    try {
        let csvContent = 'Latitude,Longitude,Surface,PlusCode\n';
        for (const pt of window.currentGeoData) {
            csvContent += `${pt.lat},${pt.lon},${pt.surface},${pt.plusCode}\n`;
        }
        
        const savePath = await ipcRenderer.invoke('dialog:saveCSV');
        if (!savePath) return; // User canceled
        
        require('fs').writeFileSync(savePath, csvContent, 'utf-8');
        showToast('CSV Exported Successfully!', 'success');
    } catch (err) {
        showToast('Error saving CSV: ' + err.message, 'error');
    }
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
let currentCsvPath = null;
let currentCsvData = [];
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
        clipContainer.className = 'w-full mb-6 max-h-72 overflow-y-auto bg-[#050505] p-2 border border-[#333] shadow-inner'; // Reset grid classes

        // Define categories based on substrings/keywords
        const categories = {
            "Anomalies & Defects": ["pothole", "crack", "uneven_surface", "rutting", "shoving", "corrugation", "bleeding", "polished_aggregate", "pumping", "raveling", "stripping", "delamination"],
            "Road Surface Types": ["asphalt", "gravel", "sand", "mud", "cobblestone", "brick_paving", "concrete_pavers", "dirt_road", "macadam", "grassy_path", "wood_planks", "metal_grating", "paved_path", "unpaved_path"],
            "Obstacles & Hazards": ["water", "bump", "cushion", "rumble_strips", "table", "manhole", "drain", "grate", "leaves", "branches", "ice", "snow", "glass", "metal_plate", "rail_tracks", "tree_root", "cone", "bollard", "barrier", "fallen_tree", "debris", "plastic_bag", "trash_can", "spill", "patch"],
            "Infrastructure & Signs": ["lines", "marking", "crosswalk", "tactile_paving", "curb", "shadow", "light", "sign", "stop", "station"],
            "Vehicles (Cars/Trucks)": ["car", "truck", "van", "suv", "jeep", "crossover", "sedan", "coupe", "convertible", "hatchback", "wagon", "sweeper", "plow", "vehicle"],
            "Other Road Users": ["bicycle", "pedestrian", "dog", "cat", "squirrel", "motorcycle", "bus", "scooter"],
            "Uncategorized": [] // Fallback
        };

        const categorizedClasses = {};
        for (const cat in categories) categorizedClasses[cat] = [];

        targetClasses.forEach(cls => {
            const clsName = cls.split(' - ')[1] || cls;
            let matched = false;
            for (const [catName, keywords] of Object.entries(categories)) {
                if (catName === "Uncategorized") continue;
                if (keywords.some(kw => clsName.toLowerCase().includes(kw))) {
                    categorizedClasses[catName].push(cls);
                    matched = true;
                    break;
                }
            }
            if (!matched) categorizedClasses["Uncategorized"].push(cls);
        });

        // Build the accordion UI for each category
        for (const [catName, classes] of Object.entries(categorizedClasses)) {
            if (classes.length === 0) continue;

            const categoryBox = document.createElement('div');
            categoryBox.className = 'collapse collapse-arrow bg-transparent border border-[#222] rounded-none mb-2';
            
            const catHeader = document.createElement('input');
            catHeader.type = 'checkbox';
            catHeader.checked = true; // start open

            const catTitle = document.createElement('div');
            catTitle.className = 'collapse-title text-xs font-semibold uppercase tracking-widest text-[#888] bg-[#111] min-h-0 p-2 flex items-center justify-between';
            catTitle.innerHTML = `<span>${catName} (${classes.length})</span>`;

            const catContent = document.createElement('div');
            catContent.className = 'collapse-content p-4 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2';

            classes.forEach(cls => {
                const wrapper = document.createElement('div');
                wrapper.className = 'flex items-center gap-2 mb-1';
                wrapper.innerHTML = `
                    <input type="checkbox" id="clip-cls-${cls}" value="${cls}" checked class="checkbox checkbox-xs checkbox-primary clip-class-checkbox" />
                    <label for="clip-cls-${cls}" class="text-[10px] sm:text-xs truncate text-[#e0e0e0] cursor-pointer" title="${cls}">${cls}</label>
                `;
                catContent.appendChild(wrapper);
            });

            categoryBox.appendChild(catHeader);
            categoryBox.appendChild(catTitle);
            categoryBox.appendChild(catContent);
            clipContainer.appendChild(categoryBox);
        }

        // Search Logic
        const searchInput = document.getElementById('search-clip-classes');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const term = e.target.value.toLowerCase();
                const categories = clipContainer.querySelectorAll('.collapse');
                categories.forEach(cat => {
                    let hasVisible = false;
                    const items = cat.querySelectorAll('.flex.items-center.gap-2');
                    items.forEach(item => {
                        const lbl = item.querySelector('label').innerText.toLowerCase();
                        if (lbl.includes(term)) {
                            item.style.display = 'flex';
                            hasVisible = true;
                        } else {
                            item.style.display = 'none';
                        }
                    });
                    
                    // Show or hide the whole category based on matches
                    if (hasVisible) {
                        cat.style.display = 'block';
                        cat.querySelector('.collapse-content').style.display = 'grid'; // keep contents open when searching
                    } else {
                        cat.style.display = 'none';
                    }
                });
            });
        }

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
  const { ipcRenderer } = require('electron');
  const file = await ipcRenderer.invoke('dialog:openModel');
  if (file) {
    document.getElementById('trainResumePath').value = file;
  }
};

window.chooseMetricsFile = async function() {
    const { ipcRenderer } = require('electron');
    const filePath = await ipcRenderer.invoke('dialog:openMetrics');
    if (filePath) {
        document.getElementById('analyticsFilePath').value = filePath;
        
        try {
            const fs = require('fs');
            const data = fs.readFileSync(filePath, 'utf-8');
            const metrics = JSON.parse(data);
            
            showToast('Metrics loaded & parsed successfully!', 'success');
        } catch (e) {
            console.error(e);
            showToast('Error reading metrics file.', 'error');
        }
    }
};


// Added back missing Map rendering logic
window.registerSurface = function(surfaceName) {
    if (!window.classState) window.classState = {};
    if (!window.classState[surfaceName]) {
        const colors = ['#f43f5e', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#a855f7', '#ec4899', '#06b6d4'];
        const numKeys = Object.keys(window.classState).length;
        window.classState[surfaceName] = {
            active: false,
            color: colors[numKeys % colors.length]
        };
    }
};

window.renderLegend = function() {
    const container = document.getElementById('map-legend-container');
    const controls = document.getElementById('dynamic-legend-controls');
    if (!container || !controls) return;
    
    container.classList.remove('hidden');
    container.classList.add('flex');
    controls.innerHTML = '';
    
    for (const surface in window.classState) {
        const state = window.classState[surface];
        let count = (window.currentGeoData || []).filter(d => d.surface === surface).length;
        
        const el = document.createElement('div');
        el.className = 'flex items-center justify-between group p-1 hover:bg-[#222] rounded cursor-pointer transition-colors';
        el.innerHTML = `
            <div class="flex items-center gap-2" onclick="window.toggleSurface('${surface}')">
                <input type="checkbox" ${state.active ? 'checked' : ''} class="checkbox checkbox-sm checkbox-primary rounded-sm border-gray-600 bg-[#111]" />
                <span class="text-sm text-gray-300 font-medium tracking-wide group-hover:text-white transition-colors" style="border-left: 3px solid ${state.color}; padding-left: 6px;">${surface}</span>
            </div>
            <span class="text-xs text-gray-500 font-mono">${count}</span>
        `;
        controls.appendChild(el);
    }
};

window.toggleSurface = function(surface) {
    if (window.classState[surface]) {
        window.classState[surface].active = !window.classState[surface].active;
        window.renderLegend();
        window.updateMapState();
    }
};


let distanceChartInstance = null;

function getDistance(lat1, lon1, lat2, lon2) {
    const Math_PI = Math.PI;
    const R = 6371e3; // metres
    const phi1 = lat1 * Math_PI/180;
    const phi2 = lat2 * Math_PI/180;
    const dphi = (lat2-lat1) * Math_PI/180;
    const dlambda = (lon2-lon1) * Math_PI/180;
    const a = Math.sin(dphi/2) * Math.sin(dphi/2) +
            Math.cos(phi1) * Math.cos(phi2) *
            Math.sin(dlambda/2) * Math.sin(dlambda/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

window.updateDistanceChart = function() {
    const ctx = document.getElementById('distance-canvas');
    if (!ctx) return;
    
    const distData = {};
    for (let surface in window.classState) {
        distData[surface] = 0;
    }
    
    const geo = window.currentGeoData || [];
    for (let i = 1; i < geo.length; i++) {
        const pt1 = geo[i-1];
        const pt2 = geo[i];
        if (pt1.surface === pt2.surface) {
            distData[pt1.surface] += getDistance(pt1.lat, pt1.lon, pt2.lat, pt2.lon);
        }
    }
    
    const activeSurfaces = Object.keys(window.classState).filter(s => window.classState[s].active);
    const labels = activeSurfaces;
    const data = labels.map(s => Math.round(distData[s]));
    const bgColors = labels.map(s => window.classState[s].color);
    
    if (distanceChartInstance) {
        distanceChartInstance.destroy();
    }
    
    if (typeof Chart === 'undefined') return;
    distanceChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: bgColors,
                borderWidth: 0,
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { color: '#222' }, ticks: { color: '#888' }, title: { display: true, text: 'Distance (m)', color: '#888'} },
                y: { grid: { display: false }, ticks: { color: '#888' } }
            },
            animation: { duration: 300 }
        }
    });
};

window.updateMapState = function() {
    if (!geoLayerGroup || !analyticsMap) return;
    analyticsMap.removeLayer(geoLayerGroup);
    geoLayerGroup = L.featureGroup().addTo(analyticsMap);
    
    const toggleEl = document.getElementById('map-render-toggle');
    const isLineMode = toggleEl ? toggleEl.checked : false;
    const labelEl = document.getElementById('map-render-label');
    if (labelEl) labelEl.innerText = isLineMode ? 'Mode: Line' : 'Mode: Dots';
    
    const geo = window.currentGeoData || [];
    
    if (isLineMode) {
        let currentSegment = [];
        let currentSurface = null;
        
        for (let i = 0; i < geo.length; i++) {
            const pt = geo[i];
            const state = window.classState[pt.surface];
            
            if (!state || !state.active) {
                if (currentSegment.length > 1) {
                    L.polyline(currentSegment.map(p => [p.lat, p.lon]), {
                        color: window.classState[currentSurface].color,
                        weight: 4,
                        opacity: 0.8,
                        smoothFactor: 1
                    }).bindPopup(`<b>${currentSurface}</b>`).addTo(geoLayerGroup);
                }
                currentSegment = [];
                currentSurface = null;
                continue;
            }
            
            if (currentSurface !== pt.surface) {
                if (currentSegment.length > 1) {
                    L.polyline(currentSegment.map(p => [p.lat, p.lon]), {
                        color: window.classState[currentSurface].color,
                        weight: 4,
                        opacity: 0.8,
                        smoothFactor: 1
                    }).bindPopup(`<b>${currentSurface}</b>`).addTo(geoLayerGroup);
                }
                currentSegment = [pt];
                currentSurface = pt.surface;
            } else {
                currentSegment.push(pt);
            }
        }
        
        if (currentSegment.length > 1 && currentSurface) {
            L.polyline(currentSegment.map(p => [p.lat, p.lon]), {
                color: window.classState[currentSurface].color,
                weight: 4,
                opacity: 0.8,
                smoothFactor: 1
            }).bindPopup(`<b>${currentSurface}</b>`).addTo(geoLayerGroup);
        }
        
    } else {
        const pathCoords = geo.map(pt => [pt.lat, pt.lon]);
        if (pathCoords.length > 0) {
            L.polyline(pathCoords, {
                color: '#666666',
                weight: 2,
                opacity: 0.5,
                smoothFactor: 1
            }).addTo(geoLayerGroup);
        }
        
        const activeData = geo.filter(pt => window.classState[pt.surface] && window.classState[pt.surface].active);
        for (const pt of activeData) {
            const state = window.classState[pt.surface];
            if (!state) continue;
            L.circleMarker([pt.lat, pt.lon], {
                radius: 4,
                fillColor: state.color,
                color: '#000',
                weight: 1,
                opacity: 1,
                fillOpacity: 0.8
            }).bindPopup(`<b>${pt.surface}</b><br>Code: ${pt.plusCode || 'N/A'}`).addTo(geoLayerGroup);
        }
    }
    
    if (window.updateDistanceChart) window.updateDistanceChart();
};

