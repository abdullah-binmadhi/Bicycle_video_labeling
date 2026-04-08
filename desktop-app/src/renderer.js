window.defaultClasses = ["0 - bicycle", "1 - potholes", "2 - manhole", "3 - water_puddle", "4 - uneven_surface", "5 - speed_bump", "6 - drain", "7 - crack", "8 - gravel", "9 - sand", "10 - mud", "11 - wet_leaves", "12 - dry_leaves", "13 - branches", "14 - ice", "15 - snow", "16 - glass", "17 - metal_plate", "18 - rail_tracks", "19 - cobblestone", "20 - brick_paving", "21 - concrete_pavers", "22 - tree_root", "23 - painted_lines", "24 - road_marking", "25 - crosswalk", "26 - pedestrian", "27 - dog", "28 - cat", "29 - squirrel", "30 - car", "31 - motorcycle", "32 - truck", "33 - bus", "34 - scooter", "35 - e-scooter", "36 - traffic_cone", "37 - bollard", "38 - construction_barrier", "39 - fallen_tree", "40 - debris", "41 - plastic_bag", "42 - trash_can", "43 - standing_water", "44 - oil_spill", "45 - smooth_asphalt", "46 - rough_asphalt", "47 - grate", "48 - tactile_paving", "49 - curb", "50 - shadow", "51 - street_light", "52 - traffic_light", "53 - stop_sign", "54 - yield_sign", "55 - speed_limit_sign", "56 - bus_stop", "57 - train_station", "58 - parked_car", "59 - moving_car", "60 - turning_car", "61 - reversing_car", "62 - emergency_vehicle", "63 - construction_vehicle", "64 - farm_vehicle", "65 - delivery_truck", "66 - garbage_truck", "67 - street_sweeper", "68 - snow_plow", "69 - tow_truck", "70 - flatbed_truck", "71 - semi_truck", "72 - box_truck", "73 - pickup_truck", "74 - van", "75 - minivan", "76 - suv", "77 - jeep", "78 - crossover", "79 - sedan", "80 - coupe", "81 - convertible", "82 - hatchback", "83 - station_wagon", "84 - sports_car", "85 - luxury_car", "86 - classic_car", "87 - antique_car", "88 - muscle_car", "89 - electric_car", "90 - hybrid_car", "91 - diesel_car", "92 - gas_car", "93 - hydrogen_car", "94 - fuel_cell_car", "95 - solar_car", "96 - flying_car", "97 - hover_car", "98 - submarine_car", "99 - boat_car", "100 - dirt_road", "101 - macadam", "102 - grassy_path", "103 - wood_planks", "104 - metal_grating", "105 - paved_path", "106 - unpaved_path", "107 - pothole_cluster", "108 - alligator_cracking", "109 - longitudinal_cracks", "110 - transverse_cracks", "111 - block_cracking", "112 - edge_cracking", "113 - rutting", "114 - shoving", "115 - corrugation", "116 - bleeding", "117 - polished_aggregate", "118 - pumping", "119 - raveling", "120 - stripping", "121 - delamination", "122 - patch", "123 - traverse_speed_bump", "124 - rubber_speed_bump", "125 - concrete_speed_bump", "126 - asphalt_speed_bump", "127 - wide_speed_bump", "128 - narrow_speed_bump", "129 - rumble_strips", "130 - speed_cushion", "131 - speed_table", "132 - bycicle_lane", "133 - bicycle_lane", "134 - asphalt"];
// --- Advanced UI Filtering ---


window.distanceFilterState = {};

window.getCategory = function(className) {
    if (!className) return 'Other';
    const surface_ids = [45, 46, 134, 8, 19, 20, 21, 100, 101, 103, 104, 105, 106, 9]; // asphalt, gravel, cobblestone, macadam, etc.
    const infra_ids = [18, 132, 133, 47, 48, 49, 51, 52, 53, 54, 55, 56, 57, 23, 24, 25, 36, 37, 38]; 
    const anomaly_ids = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14, 15, 16, 17, 22, 39, 40, 41, 42, 43, 44, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131];
    
    // Extract numeric ID from "134 - asphalt"
    const match = className.match(/^(\d+)\s-/);
    if (!match) return 'Other';
    const id = parseInt(match[1]);
    
    if (surface_ids.includes(id)) return 'Surfaces';
    if (infra_ids.includes(id)) return 'Infrastructure';
    if (anomaly_ids.includes(id)) return 'Anomalies';
    // Everything else (Cars, people, animals)
    return 'Other';
};


window.renderDistanceFilter = function() {
    const container = document.getElementById('distance-filter-dropdown');
    if (!container) return;
    container.innerHTML = '';
    
    const roadSurfaces = window.defaultClasses.filter(lbl => window.getCategory(lbl) === 'Surfaces');
    
    roadSurfaces.forEach(lbl => {
        if (window.distanceFilterState[lbl] === undefined) {
            window.distanceFilterState[lbl] = false;
        }
        
        const wrapper = document.createElement('label');
        wrapper.className = 'flex items-center gap-2 mb-1 p-1 hover:bg-[#222] cursor-pointer rounded';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'w-3 h-3 rounded bg-gray-700 border-gray-600 text-blue-500 cursor-pointer';
        checkbox.checked = window.distanceFilterState[lbl];
        checkbox.onchange = (e) => {
            window.distanceFilterState[lbl] = e.target.checked;
            window.updateMapState(); // map state updates the distance chart
        };
        const text = document.createElement('span');
        text.className = 'text-[10px] uppercase font-mono text-gray-300';
        text.innerText = lbl;
        wrapper.appendChild(checkbox);
        wrapper.appendChild(text);
        container.appendChild(wrapper);
    });
};


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

     const maxFramesEl = document.getElementById('clipMaxFrames');
     if (maxFramesEl && maxFramesEl.value) {
         args.push('--max_frames', maxFramesEl.value);
     }
     
     const saveFramesEl = document.getElementById('clipSaveFrames');
     if (saveFramesEl && !saveFramesEl.checked) {
         args.push('--no_save_frames');
     }
     
     const modelSelect = document.getElementById('clipModelSelect');
     if (modelSelect) {
         args.push('--model', modelSelect.value);
     }
     
     const confSlider = document.getElementById('clipConfSlider');
     if (confSlider) {
         args.push('--conf', (parseInt(confSlider.value) / 100).toString());
     }
     
     const useClip = document.getElementById('toggle-two-stage');
     if (useClip && useClip.checked) {
         args.push('--use_clip');
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
let distanceChart = null;
let scrubberInterval = null;

let analyticsMap = null;
let geoLayerGroup = null;
const { OpenLocationCode } = require('open-location-code');
const olcInstance = new OpenLocationCode();

function initAnalytics() {
    // 5.5 Distance Distribution Bar Chart
    const ctxDistBar = document.getElementById('distance-canvas');
    if(ctxDistBar && !distanceChart) {
        distanceChart = new Chart(ctxDistBar, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Total Distance per Surface (m)',
                    data: [],
                    backgroundColor: [],
                    borderWidth: 0
                }]
            },
            options: { 
                responsive: true, 
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: 'rgba(255,255,255,0.7)', font: { family: 'monospace' } },
                        grid: { color: 'rgba(255,255,255,0.1)' }
                    },
                    x: {
                        ticks: { color: 'rgba(255,255,255,0.7)', font: { family: 'monospace', size: 10 } },
                        grid: { display: false }
                    }
                },
                plugins: { legend: { display: false } }
             }
        });
    }
    
    // UI initializations for Filters
    window.renderDistanceFilter();

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


window.updateMapState = function() {
    if (!geoLayerGroup || !analyticsMap) return;
    analyticsMap.removeLayer(geoLayerGroup);
    geoLayerGroup = L.layerGroup().addTo(analyticsMap);
    
    let drawLinesMode = false;
    const toggle = document.getElementById('map-render-toggle');
    if (toggle) drawLinesMode = toggle.checked;

    const lbl = document.getElementById('map-render-label');
    if (lbl) lbl.innerText = drawLinesMode ? 'Mode: Lines' : 'Mode: Dots';
    
    const distanceAgg = {};

    // 1. ALWAYS draw a visible baseline white path so the shape of the route is intact
    const pathCoords = window.currentGeoData.map(pt => [pt.lat, pt.lon]);
    if (pathCoords.length > 0) {
        L.polyline(pathCoords, {
            color: '#ffffff', // More visible white mark
            weight: 3,
            opacity: 0.2,
            smoothFactor: 1
        }).addTo(geoLayerGroup);
    }

    let currentSegmentPoints = [];
    let currentSegmentSurface = null;
    let currentSegmentDistance = 0;

    // Helper to draw accumulated segment
    function commitSegment() {
        if (currentSegmentPoints.length > 1 && currentSegmentSurface) {
            let isVisible = window.classState[currentSegmentSurface] && window.classState[currentSegmentSurface].visible;
            if (isVisible) {
                let color = window.classState[currentSegmentSurface].color;
                let distKm = (currentSegmentDistance / 1000).toFixed(4); // Convert meters to KM
                L.polyline(currentSegmentPoints, {
                    color: color,
                    weight: 5,
                    opacity: 0.9 
                }).bindTooltip(`<b>${currentSegmentSurface}</b><br/>Segment length: ${distKm} KM`, {
                    className: 'bg-[#111] text-white border-[#333]'
                }).addTo(geoLayerGroup);
            }
        } else if (currentSegmentPoints.length === 1 && currentSegmentSurface && !drawLinesMode) {
             // Fallback for single isolated point if not in strictly line mode or if it happens to be just 1 dot
             let isVisible = window.classState[currentSegmentSurface] && window.classState[currentSegmentSurface].visible;
             if (isVisible) {
                 let color = window.classState[currentSegmentSurface].color;
                 L.circleMarker(currentSegmentPoints[0], {
                    radius: 5,
                    fillColor: color,
                    color: color,
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.8
                }).bindTooltip(`<b>${currentSegmentSurface}</b>`, {
                    className: 'bg-[#111] text-white border-[#333]'
                }).addTo(geoLayerGroup);
             }
        }
        currentSegmentPoints = [];
        currentSegmentDistance = 0;
        currentSegmentSurface = null;
    }

    for (const pt of window.currentGeoData) {
        if (!pt.surface) continue;
        let s = pt.surface;
        let dist = parseFloat(pt.distance_m || 0);
        let cat = window.getCategory(s);

        if (!distanceAgg[s]) distanceAgg[s] = 0;
        distanceAgg[s] += dist;

        let isVisible = window.classState[s] && window.classState[s].visible;

        if (drawLinesMode && cat === 'Surfaces') {
            if (s === currentSegmentSurface) {
                currentSegmentPoints.push([pt.lat, pt.lon]);
                currentSegmentDistance += dist;
            } else {
                commitSegment();
                currentSegmentSurface = s;
                currentSegmentPoints = [[pt.lat, pt.lon]];
                currentSegmentDistance = dist;
            }
        } else {
             commitSegment();
             if (isVisible) {
                 let color = window.classState[s] ? window.classState[s].color : '#fff';
                 L.circleMarker([pt.lat, pt.lon], {
                    radius: 5,
                    fillColor: color,
                    color: color,
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.8
                 }).bindTooltip(`<b>${s}</b><br/>Dist: ${dist}m`, {
                    className: 'bg-[#111] text-white border-[#333]'
                 }).addTo(geoLayerGroup);
             }
        }
    }
    commitSegment(); // Commit remaining points

    
    
    
    // Update Distance Bar Chart
    const barCtx = document.getElementById('distance-canvas'); // FIXED
    if (barCtx) {
        const labels = Object.keys(distanceAgg);
        const data = labels.map(l => distanceAgg[l]);
        const bColors = labels.map(l => (window.classState[l] && window.classState[l].color) ? window.classState[l].color : '#555');

        if (window.distanceChart) {
            window.distanceChart.data.labels = labels;
            window.distanceChart.data.datasets[0].data = data;
            window.distanceChart.data.datasets[0].backgroundColor = bColors;
            window.distanceChart.update();
        } else {
            window.distanceChart = new Chart(barCtx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Distance (m)',
                        data: data,
                        backgroundColor: bColors,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, grid: { color: '#333' } },
                        x: { grid: { display: false } }
                    }
                }
            });
        }
    }
}
window.classState[l] && window.classState[l].color) ? window.classState[l].color : '#555');

        if (window.distanceChartInstance) {
            window.distanceChartInstance.data.labels = labels;
            window.distanceChartInstance.data.datasets[0].data = data;
            window.distanceChartInstance.data.datasets[0].backgroundColor = bColors;
            window.distanceChartInstance.update();
        } else {
            window.distanceChartInstance = new Chart(barCtx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Distance (m)',
                        data: data,
                        backgroundColor: bColors,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, grid: { color: '#333' } },
                        x: { grid: { display: false } }
                    }
                }
            });
        }
    }
}

