
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
  'ensemble': path.join(rootDir, 'data_pipeline/ensemble_auto_labeler.py'),
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
  if (!consoleDisplay) {
      console.log(message);
      return;
  }
  
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
  if (scriptKey === 'ensemble') {
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
     
     if (scriptKey === 'ensemble') {
         const modelSelectEl = document.getElementById('clipModelSelect');
         if (modelSelectEl && modelSelectEl.value) {
             args.push('--model', modelSelectEl.value);
         }
         const confSliderEl = document.getElementById('clipConfSlider');
         if (confSliderEl && confSliderEl.value) {
             args.push('--conf', (parseFloat(confSliderEl.value) / 100).toFixed(2));
         }
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

    if (scriptKey === 'inference') {
      const infModel = document.getElementById('infModelPath') ? document.getElementById('infModelPath').value.trim() : "";
      const infCsv = document.getElementById('infCsvPath') ? document.getElementById('infCsvPath').value.trim() : "";
      
      if (infModel) args.push('--model', infModel);
      if (infCsv) args.push('--csv', infCsv);
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
let currentConsoleHeight = 250;
window.toggleConsole = function() {
  const wrapper = document.getElementById('console-wrapper');
  const chevron = document.getElementById('console-chevron');
  consoleOpen = !consoleOpen;
  if (consoleOpen) {
    wrapper.style.height = currentConsoleHeight + 'px';
    if(chevron) chevron.style.transform = 'rotate(0deg)';
  } else {
    wrapper.style.height = '42px'; // Height of resizer + header
    if(chevron) chevron.style.transform = 'rotate(180deg)';
  }
};

document.addEventListener('DOMContentLoaded', () => {
    const resizer = document.getElementById('console-resizer');
    const wrapper = document.getElementById('console-wrapper');
    let isResizing = false;
    let startY, startHeight;

    if (resizer && wrapper) {
        resizer.addEventListener('mousedown', (e) => {
            if (!consoleOpen) return;
            isResizing = true;
            startY = e.clientY;
            startHeight = parseInt(document.defaultView.getComputedStyle(wrapper).height, 10);
            document.body.style.cursor = 'ns-resize';
            e.preventDefault();
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            const dy = startY - e.clientY;
            let newHeight = startHeight + dy;
            
            if (newHeight < 100) newHeight = 100;
            if (newHeight > window.innerHeight * 0.85) newHeight = window.innerHeight * 0.85;
            
            wrapper.style.height = newHeight + 'px';
            currentConsoleHeight = newHeight;
        });

        document.addEventListener('mouseup', () => {
            if (isResizing) {
                isResizing = false;
                document.body.style.cursor = 'default';
            }
        });
    }
});

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

function initLeaflet(lat=51.3127, lng=9.4797) {
    if(!infMap) {
        // Corrected: HTML uses id="inf-playback-map"
        const mapContainer = document.getElementById('inf-playback-map');
        if(!mapContainer) return;
        
        infMap = L.map('inf-playback-map').setView([lat, lng], 15);
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

    // 2. Radar Chart – 7 classes matching the trained model
    const RADAR_LABELS = ['Asphalt', 'Gravel', 'Cobblestone', 'Pothole', 'Speed Bump', 'Bicycle Lane', 'Rail Tracks'];
    window._radarLabels = RADAR_LABELS;
    const radarCanvas = document.getElementById('inf-radar-chart');
    if (radarCanvas && !liveRadarChart) {
        liveRadarChart = new Chart(radarCanvas, {
            type: 'radar',
            data: {
                labels: RADAR_LABELS,
                datasets: [{
                    label: 'Confidence %',
                    data: Array(7).fill(0),
                    backgroundColor: 'rgba(168, 85, 247, 0.25)',
                    borderColor: '#a855f7',
                    pointBackgroundColor: '#a855f7',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#a855f7'
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false, animation: { duration: 200 },
                scales: { r: { min: 0, max: 100, ticks: { display: false, stepSize: 25 }, grid: { color: '#2a2a2a' }, angleLines: { color: '#333' }, pointLabels: { color: '#aaa', font: { size: 9 } } } },
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
    
    const mainSurface = pred.surface || "";
    const probabilities = pred.probabilities || {}; // {"Asphalt (Smooth)": 98.4, ...}
    const conf = pred.confidence || 0;
    
    // Derive a variance proxy: anomaly = inverse of asphalt confidence (0–100 scale → 0–1)
    const asphaltConf = probabilities['Asphalt (Smooth)'] || conf;
    const anomalyScore = Math.max(0, 100 - asphaltConf) / 100; // 0 = clean road, 1 = severe anomaly

    // 1. Update IMU Chart – amplitude scales with anomaly score
    if (liveImuChart) {
        liveImuChart.data.datasets.forEach((dataset, idx) => {
            dataset.data.shift();
            const amplitude = 2 + anomalyScore * 18;
            const noise = (Math.random() - 0.5) * anomalyScore * 8;
            let val = Math.sin(time * (6 + idx * 2)) * amplitude + noise;
            val = Math.max(-20, Math.min(20, val));
            dataset.data.push(val);
        });
        liveImuChart.update();
    }

    // 2. Update Radar – read direct class percentages from probabilities
    if (liveRadarChart) {
        // Map full label names to their display values in the radar
        const labelMap = {
            'Asphalt':      probabilities['Asphalt (Smooth)']   || 0,
            'Gravel':       probabilities['Gravel (Bumpy)']     || 0,
            'Cobblestone':  probabilities['Cobblestone (Harsh)']|| 0,
            'Pothole':      probabilities['Pothole (Anomaly)']  || 0,
            'Speed Bump':   probabilities['Speed Bump']         || 0,
            'Bicycle Lane': probabilities['Bicycle Lane']       || 0,
            'Rail Tracks':  probabilities['Rail Tracks']        || 0,
        };
        const newData = (window._radarLabels || liveRadarChart.data.labels).map(l => labelMap[l] || 0);
        liveRadarChart.data.datasets[0].data = newData;
        liveRadarChart.update();
    }

    // 3. Update Spectrogram Waterfall – frequency energy scales with anomaly score
    if (spectrogramCtx) {
        const w = spectrogramCtx.canvas.width;
        const h = spectrogramCtx.canvas.height;
        spectrogramData.shift();
        // High anomaly = high energy in lower frequency bins
        const newCol = Array(25).fill(0).map((_, i) => {
            const freqDecay = (25 - i) / 25; // low freq = high i index
            return (Math.random() * 0.3 + anomalyScore * freqDecay) * 10;
        });
        spectrogramData.push(newCol);
        
        spectrogramCtx.clearRect(0, 0, w, h);
        const colW = w / 80;
        const rowH = h / 25;
        for (let x = 0; x < 80; x++) {
            for (let y = 0; y < 25; y++) {
                const val = Math.min(10, spectrogramData[x]?.[y] || 0);
                // Thermal colormap: cold blue→warm yellow→hot red
                const t = val / 10;
                const r = Math.round(Math.min(255, t < 0.5 ? t * 2 * 255 : 255));
                const g = Math.round(Math.min(255, t < 0.5 ? t * 2 * 180 : (1 - (t - 0.5) * 2) * 180));
                const b = Math.round(Math.max(0, t < 0.5 ? 255 - t * 2 * 255 : 0));
                spectrogramCtx.fillStyle = `rgb(${r},${g},${b})`;
                spectrogramCtx.fillRect(x * colW, h - (y + 1) * rowH, colW + 1, rowH + 1);
            }
        }
    }

    // 4. Update Vector Ball – ball deflection proportional to anomaly score
    if (vectorBallCtx) {
        const w = vectorBallCtx.canvas.width;
        const h = vectorBallCtx.canvas.height;
        const cx = w / 2; const cy = h / 2;
        vectorBallCtx.clearRect(0, 0, w, h);
        
        // Grid lines
        vectorBallCtx.strokeStyle = '#2a2a2a';
        vectorBallCtx.lineWidth = 1;
        vectorBallCtx.beginPath();
        vectorBallCtx.moveTo(cx, 0); vectorBallCtx.lineTo(cx, h);
        vectorBallCtx.moveTo(0, cy); vectorBallCtx.lineTo(w, cy);
        vectorBallCtx.stroke();
        vectorBallCtx.beginPath(); vectorBallCtx.arc(cx, cy, Math.min(cx, cy) * 0.6, 0, 2 * Math.PI);
        vectorBallCtx.stroke();
        
        const maxDeflect = Math.min(cx, cy) * 0.8;
        const dx = (Math.random() - 0.5) * 2 * anomalyScore * maxDeflect;
        const dy = (Math.random() - 0.5) * 2 * anomalyScore * maxDeflect;
        
        // Ball color: green=smooth, yellow=moderate, red=severe
        const ballColor = anomalyScore < 0.1 ? '#10b981' : anomalyScore < 0.4 ? '#f59e0b' : '#ef4444';
        
        vectorBallCtx.beginPath();
        vectorBallCtx.arc(cx + dx, cy + dy, 7, 0, 2 * Math.PI);
        vectorBallCtx.fillStyle = ballColor;
        vectorBallCtx.shadowBlur = 12; vectorBallCtx.shadowColor = ballColor;
        vectorBallCtx.fill();
        vectorBallCtx.shadowBlur = 0;
    }

    // 5. Update Severity Bar – driven by non-road probability
    const sevBar = document.getElementById('inf-severity-bar');
    if (sevBar) {
        const nonRoadConf = 100 - (probabilities['Asphalt (Smooth)'] || 0) - (probabilities['Bicycle Lane'] || 0);
        const pct = Math.max(0, Math.min(100, nonRoadConf));
        sevBar.style.width = pct + '%';
        sevBar.style.backgroundColor = pct > 50 ? '#ef4444' : (pct > 20 ? '#f59e0b' : '#10b981');
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
        // Load GPS route from predictions.json to power the live map
        let gpsLatlngs = [];
        let gpsData = [];
        try {
            const predPath = require('path').join(__dirname, '../../predictions.json');
            if (require('fs').existsSync(predPath)) {
                const preds = JSON.parse(require('fs').readFileSync(predPath, 'utf8'));
                const validPreds = preds.filter(p => p.lat && p.lng && !isNaN(p.lat) && !isNaN(p.lng));
                gpsLatlngs = validPreds.map(p => [p.lat, p.lng]);
                gpsData = validPreds;
            }
        } catch(e) {}
        
        // Use real GPS coords if available, else fall back to mock
        const firstLat = gpsLatlngs.length > 0 ? gpsLatlngs[0][0] : 51.3127;
        const firstLng = gpsLatlngs.length > 0 ? gpsLatlngs[0][1] : 9.4797;
        
        if(typeof initLeaflet === 'function') initLeaflet(firstLat, firstLng);
        
        if(typeof infMap !== 'undefined' && infMap) {
            let latlngs = gpsLatlngs;
            if (latlngs.length < 2) {
                // Fallback mock route
                latlngs = [];
                gpsData = [];
                let curl = firstLat, curlg = firstLng;
                for(let i = 0; i < 150; i++) {
                    latlngs.push([curl, curlg]);
                    gpsData.push({lat: curl, lng: curlg, surface: 'Unknown'});
                    curl += (Math.sin(i * 0.1) - 0.5) * 0.0004;
                    curlg += (Math.cos(i * 0.2) + 0.5) * 0.0004;
                }
            }
            window.infLatlngs = latlngs;
            
            // Clear old layers from infMap except the tile layer to avoid duplicates
            infMap.eachLayer((layer) => {
                if (!layer._url) { // Not a tile layer
                    infMap.removeLayer(layer);
                }
            });
            
            // Draw background trace line
            L.polyline(latlngs, {color: '#666666', weight: 2, opacity: 0.5}).addTo(infMap);
            
            // Draw colored segments
            for (const pt of gpsData) {
                let surf = pt.surface || 'Unclassified';
                if (typeof window.registerSurface === 'function') window.registerSurface(surf);
                
                const color = (window.classState && window.classState[surf]) ? window.classState[surf].color : '#10b981';
                
                L.circleMarker([pt.lat, pt.lng], {
                    radius: 3,
                    fillColor: color,
                    color: color,
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.8
                }).addTo(infMap);
            }
            
            mapMarker = null; // Reset tracker so it gets re-rendered
            infMap.fitBounds(L.latLngBounds(latlngs), { padding: [12, 12] });
            setTimeout(() => infMap.invalidateSize(), 350);
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
    
    // Load Auto Annotation Labels if provided
    let frameAnnotations = [];
    const infLabelInput = document.getElementById('infLabelPath');
    if (infLabelInput && infLabelInput.value && require('fs').existsSync(infLabelInput.value)) {
        try {
            const csvData = require('fs').readFileSync(infLabelInput.value, 'utf8');
            const lines = csvData.trim().split('\n');
            let minRawTime = Number.MAX_VALUE;

            if (lines.length > 0) {
                // Check headers to assign dynamic indices
                const headers = lines[0].toLowerCase().split(',').map(h => h.trim());
                
                // Fallbacks matching old legacy offsets
                let idxFrame = 0, idxLabel = 1, idxConf = 2, idxX1 = 3, idxY1 = 4, idxX2 = 5, idxY2 = 6;
                
                let maybeFrame = headers.findIndex(h => h.includes('image_id') || h.includes('frame'));
                if (maybeFrame !== -1) idxFrame = maybeFrame;
                
                let maybeLabel = headers.findIndex(h => h === 'class_name' || h === 'class');
                if (maybeLabel === -1) maybeLabel = headers.findIndex(h => h.includes('label') && !h.includes('code'));
                if (maybeLabel !== -1) idxLabel = maybeLabel;
                
                let maybeConf = headers.findIndex(h => h.includes('score') || h.includes('conf'));
                if (maybeConf !== -1) idxConf = maybeConf;
                
                let tmpX1 = headers.findIndex(h => h === 'xmin' || h === 'x1'); if(tmpX1 !== -1) idxX1 = tmpX1;
                let tmpY1 = headers.findIndex(h => h === 'ymin' || h === 'y1'); if(tmpY1 !== -1) idxY1 = tmpY1;
                let tmpX2 = headers.findIndex(h => h === 'xmax' || h === 'x2'); if(tmpX2 !== -1) idxX2 = tmpX2;
                let tmpY2 = headers.findIndex(h => h === 'ymax' || h === 'y2'); if(tmpY2 !== -1) idxY2 = tmpY2;

                // Process data rows
                lines.slice(1).forEach(line => {
                    if(!line.trim()) return;
                    const p = line.split(',').map(v => v.trim());
                    if(p.length >= 7) {
                        const frameStr = p[idxFrame] || '';
                        const match = frameStr.match(/frame_([\d.]+)\.jpg/);
                        let rawTime = 0;
                        if (match) rawTime = parseFloat(match[1]);
                        
                        if (rawTime > 0) minRawTime = Math.min(minRawTime, rawTime);

                        const x1 = parseFloat(p[idxX1]);
                        const y1 = parseFloat(p[idxY1]);
                        const x2 = parseFloat(p[idxX2]);
                        const y2 = parseFloat(p[idxY2]);

                        let conf = parseFloat(p[idxConf]);
                        if (isNaN(conf)) conf = 0;

                        frameAnnotations.push({
                            rawTime: rawTime,
                            timestamp: 0,
                            label: p[idxLabel] || "Unknown",
                            confidence: conf,
                            x: x1,
                            y: y1,
                            w: Math.max(0, x2 - x1),
                            h: Math.max(0, y2 - y1)
                        });
                    }
                });
            }
            // Align timestamps relative to the earliest frame being T=0
            if (minRawTime !== Number.MAX_VALUE) {
                frameAnnotations.forEach(a => a.timestamp = Math.max(0, a.rawTime - minRawTime));
            }
        } catch(err) {
            console.error("Error loading Label CSV", err);
        }
    }

    if (window.aiInterval) clearInterval(window.aiInterval);
    window.aiInterval = setInterval(() => {
        if(!vidPlayer.paused) {
           const currentTime = vidPlayer.currentTime; // seconds into the video
           const videoDuration = vidPlayer.duration || 66; // fallback 66s based on recording
           
           // ── Prediction lookup ─────────────────────────────────────────────
           // predictions.json spans the entire IMU recording (0–3299s).
           // Map video playback position proportionally to the predictions array.
           if (predictions.length > 0) {
               let currentPred;
               if (videoDuration && videoDuration > 1) {
                   // Proportional mapping: video progress → predictions index
                   const progress = Math.max(0, Math.min(1, currentTime / videoDuration));
                   const idx = Math.floor(progress * (predictions.length - 1));
                   currentPred = predictions[idx];
               } else {
                   // Fallback: direct timestamp search (works if video and IMU are synchronized)
                   currentPred = predictions.find(p => p.timestamp <= currentTime && (p.timestamp + 1) > currentTime);
               }
               if(currentPred) {
                   window.updateLiveDashboard(currentPred, currentTime);
                   label.innerText = currentPred.surface.toUpperCase();
                   if(currentPred.surface.includes('Asphalt'))
                       label.className = 'text-2xl font-black tracking-widest text-emerald-400 switch-anim';
                   else if(currentPred.surface.includes('Gravel') || currentPred.surface.includes('Cobblestone'))
                       label.className = 'text-2xl font-black tracking-widest text-yellow-400 switch-anim';
                   else if(currentPred.surface.includes('Bicycle') || currentPred.surface.includes('Rail'))
                       label.className = 'text-2xl font-black tracking-widest text-cyan-400 switch-anim';
                   else
                       label.className = 'text-2xl font-black tracking-widest text-rose-400 switch-anim';
               }
           }
           
           // ── Bounding box overlay ──────────────────────────────────────────
           const canvas = document.getElementById('inf-overlay-canvas');
           if (canvas) {
               canvas.classList.remove('hidden');
               if (canvas.width !== vidPlayer.clientWidth || canvas.height !== vidPlayer.clientHeight) {
                   canvas.width = vidPlayer.clientWidth;
                   canvas.height = vidPlayer.clientHeight;
               }
               
               const ctx = canvas.getContext('2d');
               ctx.clearRect(0, 0, canvas.width, canvas.height);
               
               if (frameAnnotations.length > 0) {
                   const rawVidW = vidPlayer.videoWidth || 1920;
                   const rawVidH = vidPlayer.videoHeight || 1080;
                   const scaleX = canvas.width / rawVidW;
                   const scaleY = canvas.height / rawVidH;
                   
                   // Map video playback position proportionally to the annotations array.
                   // Frame filenames have an 8-hour UTC offset vs IMU NTP, so we avoid
                   // direct timestamp subtraction and instead use proportional indexing.
                   const vidProgress   = Math.max(0, Math.min(1, currentTime / videoDuration));
                   const annoIdx       = Math.floor(vidProgress * (frameAnnotations.length - 1));
                   // Show a small window of nearby annotations (±3 frames at 30fps ≈ 0.1s window)
                   const windowSize    = Math.max(1, Math.floor(frameAnnotations.length * (0.1 / videoDuration)));
                   const start         = Math.max(0, annoIdx - windowSize);
                   const end           = Math.min(frameAnnotations.length - 1, annoIdx + windowSize);
                   const currentAnnos  = frameAnnotations.slice(start, end + 1);
                   
                   currentAnnos.forEach(a => {
                       const drawX = a.x * scaleX;
                       const drawY = a.y * scaleY;
                       const drawW = a.w * scaleX;
                       const drawH = a.h * scaleY;
                       if (drawW < 5 || drawH < 5) return; // skip degenerate boxes
                       
                       ctx.strokeStyle = '#a855f7';
                       ctx.lineWidth = 2;
                       ctx.strokeRect(drawX, drawY, drawW, drawH);
                       
                       const cleanLabel = a.label.trim();
                       const textW = ctx.measureText(cleanLabel).width + 16;
                       ctx.fillStyle = 'rgba(168,85,247,0.85)';
                       ctx.fillRect(drawX, Math.max(0, drawY - 22), textW, 22);
                       ctx.fillStyle = '#FFFFFF';
                       ctx.font = 'bold 11px monospace';
                       ctx.fillText(cleanLabel, drawX + 8, Math.max(14, drawY - 6));
                   });
               }
           }
        }
    }, 50); // 20fps tick rate
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
        }).setView([51.3127, 9.4797], 13);
        
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



window.currentGeoData = [];

const ALLOWED_LABELS = {
    "bicycle": "1",
    "person": "2",
    "car": "3",
    "motorcycle": "4",
    "bus": "5",
    "truck": "6",
    "traffic light": "7",
    "stop sign": "8"
};

const REVERSE_LABELS = Object.fromEntries(
    Object.entries(ALLOWED_LABELS).map(([k, v]) => [v, k])
);

function normalizeLabel(rawLabel) {
    if (!rawLabel) return 'Unclassified';
    
    let labelLower = rawLabel.trim().toLowerCase();
    
    // Strip numeric prefixes if formatted like "3 - car"
    const match = labelLower.match(/^\d+\s*-\s*(.+)$/);
    if (match) {
        labelLower = match[1];
    }
    
    // Handle specific mappings
    if (labelLower.includes('bike')) labelLower = 'bicycle';
    if (labelLower.includes('pedestrian')) labelLower = 'person';
    if (labelLower.includes('automobile')) labelLower = 'car';
    if (labelLower.includes('lorry')) labelLower = 'truck';
    
    if (ALLOWED_LABELS[labelLower]) {
        return labelLower;
    }
    
    if (REVERSE_LABELS[labelLower]) {
        return REVERSE_LABELS[labelLower];
    }
    
    return 'Unclassified';
}

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
                let rawSurface = classIdx !== -1 && cols[classIdx] ? cols[classIdx] : '';
                let surfaceType = normalizeLabel(rawSurface);
                
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
            let rawSurface = classIdx !== -1 && row[classIdx] ? row[classIdx] : '';
            let surface = normalizeLabel(rawSurface);
            
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

// 1. Manual Annotation Saving Handler
let currentManualBox = null;

window.saveManualAnnotation = function() {
  const promptInput = document.getElementById('interactive-clip-prompt');
  const videoPlayer = document.getElementById('video-player');
  const canvas = document.getElementById('annotation-layer');
  
  if (!promptInput.value) {
      showToast('Please type a label name first.', 'error');
      return;
  }
  
  if (!currentManualBox) {
      showToast('Please draw a bounding box on the video first.', 'error');
      return; 
  }
  
  if (!videoPlayer || !videoPlayer.src) {
      showToast('Please map a master video first prior to saving.', 'error');
      return; 
  }

  const videoPath = document.getElementById('annoVideoPath').value;
  const rawVidW = videoPlayer.videoWidth || 1920; 
  const rawVidH = videoPlayer.videoHeight || 1080;
  
  // Calculate correct scaling accounting for object-fit: contain
  const vidRatio = rawVidW / rawVidH;
  const canvasRatio = canvas.width / canvas.height;
  
  let renderW = canvas.width;
  let renderH = canvas.height;
  let offsetX = 0;
  let offsetY = 0;
  
  if (canvasRatio > vidRatio) {
      // Pillarboxing (black bars on sides)
      renderW = canvas.height * vidRatio;
      offsetX = (canvas.width - renderW) / 2;
  } else if (canvasRatio < vidRatio) {
      // Letterboxing (black bars on top/bottom)
      renderH = canvas.width / vidRatio;
      offsetY = (canvas.height - renderH) / 2;
  }

  const { startX, startY, width, height } = currentManualBox;
  
  // Map coordinates removing the offset bars, scaling relative to raw video
  const realX = Math.round((startX - offsetX) * (rawVidW / renderW));
  const realY = Math.round((startY - offsetY) * (rawVidH / renderH));
  const realW = Math.round(width * (rawVidW / renderW));
  const realH = Math.round(height * (rawVidH / renderH));
  
  let label = promptInput.value;
  const currentTime = videoPlayer.currentTime;
  
  const fs = require('fs');
  const path = require('path');
  
  // Use the selected Output Folder if one is set, else default to project root
  const outputDir = (typeof manualCaptureFolder !== 'undefined' && manualCaptureFolder) 
      ? manualCaptureFolder 
      : path.join(__dirname, '../../');
  
  // Format for ML pipeline: image_id, label_code, class_name, xmin, ymin, xmax, ymax, score
  const xmax = realX + realW;
  const ymax = realY + realH;

  // Use IIFE to allow await inside a non-async function
  (async () => {
    const success = await require('electron').ipcRenderer.invoke('save-master-annotation', {
        image_id: videoPath + '_frame_' + currentTime.toFixed(3),
        class_name: label,
        score: 1.0,
        bbox: [realX, realY, xmax, ymax],
        masterDir: outputDir
    });

    if (success) {
        logToConsole(`[Manual Annotation] Saved via IPC: [${realX}, ${realY}, ${xmax}, ${ymax}] as '${label}'`);
        showToast(`Annotation '${label}' saved successfully to master_annotations.csv.`, 'success');
    } else {
        showToast('Error saving to master annotations via Backend.', 'error');
    }
  })();

  // Draw final saved bubble
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#F43F5E';
  ctx.fillRect(startX, Math.max(0, startY - 24), ctx.measureText(label).width + 16, 24);
  ctx.fillStyle = '#FFFFFF';
  ctx.font = 'bold 12px monospace';
  ctx.fillText(label, startX + 8, Math.max(0, startY - 24) + 16);
  
  currentManualBox = null;
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
        
        // Ensure width/height are positive values from top-left logic
        let finalStartX = Math.min(startX, endX);
        let finalStartY = Math.min(startY, endY);
        let finalW = Math.abs(endX - startX);
        let finalH = Math.abs(endY - startY);
        
        if (finalW > 10 && finalH > 10) {
            currentManualBox = {
                startX: finalStartX,
                startY: finalStartY,
                width: finalW,
                height: finalH
            };
            logToConsole(`[Manual Annotation] Bounding box locked: [${finalStartX.toFixed(1)}, ${finalStartY.toFixed(1)}, ${finalW.toFixed(1)}, ${finalH.toFixed(1)}]. Waiting for label text...`);
            showToast('Box locked. Now type a label and click Save Annotation.', 'success');
        } else {
            ctx.clearRect(0, 0, canvas.width, canvas.height); // Too small, clear it
            currentManualBox = null;
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

            // Try to load persisted annotations from master_annotations.csv
            const imagePath = currentDatasetImages[index];
            const imageDir = require('path').dirname(imagePath);
            const csvPath = require('path').join(imageDir, 'master_annotations.csv');
            try {
                if (require('fs').existsSync(csvPath)) {
                    const raw = require('fs').readFileSync(csvPath, 'utf8').trim();
                    const rows = raw.split('\n');
                    if (rows.length > 1) {
                        const headers = rows[0].split(',').map(h => h.trim().toLowerCase());
                        const idxId    = headers.indexOf('image_id');
                        const idxCls   = headers.indexOf('class_name');
                        const idxXmin  = headers.indexOf('xmin');
                        const idxYmin  = headers.indexOf('ymin');
                        const idxXmax  = headers.indexOf('xmax');
                        const idxYmax  = headers.indexOf('ymax');
                        const idxScore = headers.indexOf('score');

                        rows.slice(1).forEach(row => {
                            if (!row.trim()) return;
                            const cols = row.split(',').map(c => c.trim());
                            if (cols[idxId] !== imagePath) return; // only this image
                            const xmin = parseFloat(cols[idxXmin]);
                            const ymin = parseFloat(cols[idxYmin]);
                            const xmax = parseFloat(cols[idxXmax]);
                            const ymax = parseFloat(cols[idxYmax]);
                            if (isNaN(xmin) || isNaN(ymin) || isNaN(xmax) || isNaN(ymax)) return;

                            // Convert image-pixel coords to canvas-display coords after image loads
                            // We store raw image coords first, then scale in onload below
                            currentBoxes.push({
                                _imgX: xmin, _imgY: ymin, _imgW: xmax - xmin, _imgH: ymax - ymin,
                                label: cols[idxCls] || 'unknown',
                                score: idxScore !== -1 ? parseFloat(cols[idxScore]) : 1.0,
                                colorBox: '#00bfff',    // Persistent annotations styled in blue
                                colorFont: '#ffffff',
                                thickness: 2,
                                opacity: 100,
                                _persisted: true
                            });
                        });
                    }
                }
            } catch (e) {
                console.warn('[Dataset Gallery] Could not read master_annotations.csv:', e);
            }

            if (datasetAnnotationCanvas.width > 0) {
                renderDatasetCanvas();
            }
            if (datasetLabelSelect) datasetLabelSelect.value = "0 - bicycle";
        }
    }

    // After image loads, scale _img* coords from image-space into canvas-display-space
    datasetPreviewImg.onload = () => {
        datasetAnnotationCanvas.width  = datasetPreviewImg.clientWidth;
        datasetAnnotationCanvas.height = datasetPreviewImg.clientHeight;

        const imgW = datasetPreviewImg.naturalWidth  || datasetPreviewImg.clientWidth;
        const imgH = datasetPreviewImg.naturalHeight || datasetPreviewImg.clientHeight;
        const scaleX = datasetAnnotationCanvas.width  / imgW;
        const scaleY = datasetAnnotationCanvas.height / imgH;

        currentBoxes.forEach(box => {
            if (box._persisted) {
                box.x = box._imgX * scaleX;
                box.y = box._imgY * scaleY;
                box.w = box._imgW * scaleX;
                box.h = box._imgH * scaleY;
            }
        });

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
        // Don't show toast if 0 boxes, just allow saving 0 boxes (which means clearing the image)

        const imagePath = currentDatasetImages[currentDatasetIndex];
        const imageDir = require('path').dirname(imagePath);

        const payloadBoxes = [];

        for (const box of currentBoxes) {
            // Convert canvas display coordinates to xmin,ymin,xmax,ymax
            // Canvas dimensions match the display image - scale to image pixel space
            const imgW = datasetPreviewImg.naturalWidth || datasetPreviewImg.clientWidth;
            const imgH = datasetPreviewImg.naturalHeight || datasetPreviewImg.clientHeight;
            const scaleX = imgW / datasetAnnotationCanvas.width;
            const scaleY = imgH / datasetAnnotationCanvas.height;

            const xmin = Math.round(box.x * scaleX);
            const ymin = Math.round(box.y * scaleY);
            const xmax = Math.round((box.x + box.w) * scaleX);
            const ymax = Math.round((box.y + box.h) * scaleY);

            payloadBoxes.push({
                class_name: box.label || 'unknown',
                score: 1.0,
                bbox: [xmin, ymin, xmax, ymax]
            });
        }

        const ok = await ipcRenderer.invoke('sync-image-annotations', {
            image_id: imagePath,
            boxes: payloadBoxes,
            masterDir: imageDir
        });

        if (ok) {
            const savedCount = payloadBoxes.length;
            logToConsole(`[Dataset Gallery] Synced ${savedCount} annotation(s) for: ${imagePath}`);
            btnDatasetSave.innerHTML = `SAVED ${savedCount} BOX${savedCount === 1 ? '' : 'ES'}!`;
            setTimeout(() => btnDatasetSave.innerHTML = "[SAVE] Overwrite Frame", 2000);
            showToast(`Synchronized ${savedCount} annotation(s) to master_annotations.csv`, 'success');
        } else {
            showToast('Failed to save annotations. Check console.', 'error');
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
            "Infrastructure & Signs": ["lines", "marking", "crosswalk", "tactile_paving", "curb", "shadow", "light", "sign", "stop", "station", "lane", "bicycle_lane"],
            "Vehicles (Cars/Trucks)": ["car", "truck", "van", "suv", "jeep", "crossover", "sedan", "coupe", "convertible", "hatchback", "wagon", "sweeper", "plow", "vehicle"],
            "Other Road Users": ["bicycle", "pedestrian", "dog", "cat", "squirrel", "motorcycle", "bus", "scooter"]
        };

        const categorizedClasses = {};
        for (const cat in categories) categorizedClasses[cat] = [];

        targetClasses.forEach(cls => {
            const clsName = cls.split(' - ')[1] || cls;
            let matched = false;
            for (const [catName, keywords] of Object.entries(categories)) {
                if (keywords.some(kw => clsName.toLowerCase().includes(kw))) {
                    categorizedClasses[catName].push(cls);
                    matched = true;
                    break;
                }
            }
            if (!matched) categorizedClasses["Infrastructure & Signs"].push(cls);
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

            // Fix canvas scale stretching by removing implicit letterboxing scaling differences
            const vidRatio = rawVidW / rawVidH;
            const canvasRatio = annotationLayer.width / annotationLayer.height;
            
            let renderW = annotationLayer.width;
            let renderH = annotationLayer.height;
            let offsetX = 0;
            let offsetY = 0;
            
            if (canvasRatio > vidRatio) {
                // Pillarboxing
                renderW = annotationLayer.height * vidRatio;
                offsetX = (annotationLayer.width - renderW) / 2;
            } else if (canvasRatio < vidRatio) {
                // Letterboxing
                renderH = annotationLayer.width / vidRatio;
                offsetY = (annotationLayer.height - renderH) / 2;
            }

            // Draw annotations on top, perfectly extracting only the portion overlaying the video
            hCtx.drawImage(
                annotationLayer, 
                offsetX, offsetY, renderW, renderH, // source crop
                0, 0, rawVidW, rawVidH              // destination rect
            );

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

