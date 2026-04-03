import re

js_path = 'desktop-app/src/renderer.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Replace the block for train
old_block = """    if (scriptKey === 'train') {
        const customTrainData = document.getElementById('trainDataPath') ? document.getElementById('trainDataPath').value.trim() : "";
        if (customTrainData) {
            args.push('--dataset', customTrainData);
        }
    }"""

new_block = """    if (scriptKey === 'train') {
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
    }"""

js = js.replace(old_block, new_block)

# Add initLossChart if it's not there
lossChartLogic = """
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
        logToConsole(`\n[System] Process violently terminated.\n`);
    }
}
"""
if "window.initLossChart =" not in js:
    js += "\n" + lossChartLogic


# Modify process spawn block correctly
old_spawn = """    const pythonProcess = spawn(config.condaPython, args, {"""

new_spawn = """    const pythonProcess = spawn(config.condaPython, args, {
      cwd: config.workspaceRoot
    });
    if (scriptKey === 'train') window.activeTrainingProcess = pythonProcess;
"""

if "window.activeTrainingProcess = pythonProcess;" not in js:
     js = js.replace(old_spawn, new_spawn)

# Replace stdout parser
old_parser = """    pythonProcess.stdout.on('data', (data) => {
        logToConsole(data.toString());
        const strData = data.toString();
        
        // --- LIVE SYNC STATS INTERCEPT ---
        if (scriptKey === 'sync' && strData.includes('SYNC_STATS:')) {"""

new_parser = """    pythonProcess.stdout.on('data', (data) => {
        const strData = data.toString();
        logToConsole(strData);
        
        // --- LIVE SYNC STATS INTERCEPT ---
        if (scriptKey === 'sync' && strData.includes('SYNC_STATS:')) {
            const lines = strData.split('\\n');
            lines.forEach(l => {
                if (l.includes('SYNC_STATS:')) {
                    try {
                        const jsonStr = l.split('SYNC_STATS:')[1].trim();
                        const stats = JSON.parse(jsonStr);
                        document.getElementById('sync-analytics-board').classList.remove('hidden');
                        document.getElementById('sync-stat-rows').innerText = stats.final_rows.toLocaleString();
                        
                        const dropPct = (stats.dropped_percent || 0).toFixed(1);
                        const dropEl = document.getElementById('sync-stat-drops');
                        dropEl.innerText = `${dropPct}%`;
                        dropEl.className = dropPct > 5 ? "text-xl font-bold font-mono text-amber-500" : "text-xl font-bold font-mono text-emerald-500";
                        
                        const classBoard = document.getElementById('sync-stat-classes');
                        classBoard.innerHTML = '';
                        if (stats.class_counts) {
                            Object.entries(stats.class_counts).forEach(([c, count]) => {
                                classBoard.innerHTML += `<div class="badge badge-outline border-[#333] text-slate-300 text-xs">${c}: ${count}</div>`;
                            });
                        }
                    } catch(e) {}
                }
            });
        }
        
        // --- LIVE TRAIN STATS INTERCEPT ---
        if (scriptKey === 'train' && strData.includes('EPOCH_STATS:')) {
            const lines = strData.split('\\n');
            lines.forEach(l => {
                if (l.includes('EPOCH_STATS:')) {
                    try {
                        const jsonStr = l.split('EPOCH_STATS:')[1].trim();
                        const stats = JSON.parse(jsonStr);
                        const tEpoch = document.getElementById('stat-epoch');
                        if(tEpoch) tEpoch.innerText = stats.epoch;
                        
                        const valLoss = stats.val_loss || stats.train_loss;
                        const tLoss = document.getElementById('stat-loss');
                        if (tLoss && valLoss) tLoss.innerText = valLoss.toFixed(4);
                        
                        if (window.lossChartInstance && valLoss !== undefined) {
                           window.lossChartInstance.data.labels.push(`Ep ${stats.epoch}`);
                           window.lossChartInstance.data.datasets[0].data.push(stats.train_loss);
                           window.lossChartInstance.data.datasets[1].data.push(valLoss);
                           window.lossChartInstance.update();
                        }
                    } catch (e) { console.error(e); }
                }
            });
        }
"""
if "LIVE TRAIN STATS" not in js:
    # Use regex to find the start of the stdout block and replace down through the sync block
    js = js.replace("""    pythonProcess.stdout.on('data', (data) => {
        logToConsole(data.toString());
        const strData = data.toString();
        
        // --- LIVE SYNC STATS INTERCEPT ---
        if (scriptKey === 'sync' && strData.includes('SYNC_STATS:')) {""", new_parser.replace("""    pythonProcess.stdout.on('data', (data) => {
        const strData = data.toString();
        logToConsole(strData);
        
        // --- LIVE SYNC STATS INTERCEPT ---
        if (scriptKey === 'sync' && strData.includes('SYNC_STATS:')) {""",""))

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("Fix successfully applied!")
