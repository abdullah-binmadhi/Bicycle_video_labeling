import re

js_path = 'desktop-app/src/renderer.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Add ipcRenderer.invoke for chooseTrainData and chooseResumeModel
funcs_to_add = """
async function chooseTrainData() {
  const result = await ipcRenderer.invoke('dialog:openFile', {
    title: 'Select Training Labels/Timeline',
    properties: ['openFile'],
    filters: [{ name: 'CSV', extensions: ['csv'] }]
  });
  if (result) document.getElementById('trainDataPath').value = result;
}

async function chooseResumeModel() {
  const result = await ipcRenderer.invoke('dialog:openFile', {
    title: 'Select PyTorch Checkpoint to Resume',
    properties: ['openFile'],
    filters: [{ name: 'Models', extensions: ['pth', 'pt'] }]
  });
  if (result) document.getElementById('trainResumePath').value = result;
}

let activeTrainingProcess = null;
let lossChartInstance = null;

function stopActiveProcess() {
  if (activeTrainingProcess) {
    activeTrainingProcess.kill();
    appendLog('Process forcefully terminated by user.');
    if (document.getElementById('spinner-train')) document.getElementById('spinner-train').classList.add('hidden');
    if (document.getElementById('btn-train-stop')) document.getElementById('btn-train-stop').classList.add('hidden');
    if (document.getElementById('btn-train')) document.getElementById('btn-train').disabled = false;
  }
}
"""
if "async function chooseResumeModel()" not in js:
    js = js.replace("async function chooseConfigFile() {", funcs_to_add + "\nasync function chooseConfigFile() {")

# 2. Modify the runScript switch case for train
old_train = """    } else if (scriptKey === 'train') {
      targetScript = 'train_unified.py';
      const useVision = document.getElementById('toggle-vision').checked;
      const useImu = document.getElementById('toggle-imu').checked;
      const dataPath = document.getElementById('trainDataPath').value;

      if (!useVision && !useImu) {
        appendLog('❌ Error: At least one modality (Vision or IMU) must be enabled.');
        spinner.classList.add('hidden');
        btn.disabled = false;
        return;
      }
      if (dataPath) args.push('--data', dataPath);
      args.push('--use_vision', useVision ? 'True' : 'False');
      args.push('--use_imu', useImu ? 'True' : 'False');
    }"""

new_train = """    } else if (scriptKey === 'train') {
      targetScript = 'train_unified.py';
      // UI Modality
      const useVision = document.getElementById('toggle-vision')?.checked ?? false;
      const useImu = document.getElementById('toggle-imu')?.checked ?? true;
      const dataPath = document.getElementById('trainDataPath')?.value;
      
      // UI Hyperparameters
      const epochs = document.getElementById('train-epochs')?.value;
      const lr = document.getElementById('train-lr')?.value;
      const batch = document.getElementById('train-batch')?.value;
      const checkpoint = document.getElementById('trainResumePath')?.value;

      if (!useVision && !useImu) {
        appendLog('âŒ Error: At least one modality (Vision or IMU) must be enabled.');
        spinner.classList.add('hidden');
        btn.disabled = false;
        return;
      }
      
      if (dataPath) args.push('--data', dataPath);
      args.push('--use_vision', useVision ? 'True' : 'False');
      args.push('--use_imu', useImu ? 'True' : 'False');
      
      if (epochs) args.push('--epochs', epochs);
      if (lr) args.push('--lr', lr);
      if (batch) args.push('--batch_size', batch);
      if (checkpoint) args.push('--checkpoint', checkpoint);

      // Show stop button and stat board
      const stopBtn = document.getElementById('btn-train-stop');
      if (stopBtn) stopBtn.classList.remove('hidden');
      const statsBoard = document.getElementById('training-stats');
      if (statsBoard) statsBoard.style.display = 'grid';
      
      // Init chart
      initLossChart();

    }"""
js = js.replace(old_train, new_train)


# 3. Add chart logic and stats parser
chart_and_stats = """
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
"""

if "function initLossChart()" not in js:
    js = js + "\n" + chart_and_stats

old_stdout = """    pythonProcess.stdout.on('data', (data) => {
      const output = data.toString();
      appendLog(output.trim());
      
      // Live updates for Sync script intercept
      if (scriptKey === 'sync') {"""

new_stdout = """    pythonProcess.stdout.on('data', (data) => {
      const output = data.toString();
      appendLog(output.trim());
      
      // Live updates for Sync script intercept
      if (scriptKey === 'train' && output.includes('EPOCH_STATS:')) {
          const lines = output.split('\\n');
          lines.forEach(l => {
              if (l.includes('EPOCH_STATS:')) {
                  try {
                      const jsonStr = l.split('EPOCH_STATS:')[1];
                      const stats = JSON.parse(jsonStr);
                      // Update DOM
                      if(document.getElementById('stat-epoch')) document.getElementById('stat-epoch').innerText = stats.epoch;
                      if(document.getElementById('stat-loss')) document.getElementById('stat-loss').innerText = (stats.val_loss || stats.train_loss).toFixed(4);
                      
                      // Ping effect
                      const ping = document.getElementById('ping-epoch');
                      if(ping) { ping.classList.remove('hidden'); setTimeout(()=>ping.classList.add('hidden'), 500); }

                      // Update Chart
                      if (lossChartInstance) {
                          lossChartInstance.data.labels.push(`Ep ${stats.epoch}`);
                          lossChartInstance.data.datasets[0].data.push(stats.train_loss);
                          lossChartInstance.data.datasets[1].data.push(stats.val_loss);
                          lossChartInstance.update();
                      }

                  } catch(e) { console.error('Stat parse err', e); }
              }
          });
      }

      if (scriptKey === 'sync') {"""
js = js.replace(old_stdout, new_stdout)

# Add chartjs to index.html if not present
with open('desktop-app/src/index.html', 'r') as h: html = h.read()
if 'chart.js' not in html:
    html = html.replace('</head>', '  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>\n</head>')
    with open('desktop-app/src/index.html', 'w') as h: h.write(html)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("JS UI update successful")
