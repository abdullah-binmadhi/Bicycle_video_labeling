import re

file_path = '/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/renderer.js'
with open(file_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Add dialog helpers
dialog_append = """
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
"""
js = js.replace("window.chooseSyncDir = async function() {", dialog_append + "\nwindow.chooseSyncDir = async function() {")

# Update arg parsing for 'sync'
sync_search = """  if (scriptKey === 'sync') {
      const customDataDir = document.getElementById('syncDataPath') ? document.getElementById('syncDataPath').value.trim() : "";
      if (customDataDir) {
           args.push('--data_dir', customDataDir);
      }
  }"""

sync_replace = """  if (scriptKey === 'sync') {
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
              logToConsole("[WARN] Ad-Hoc sync requires both IMU and Label CSVs.\\n", true);
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
  }"""

if sync_search in js:
    js = js.replace(sync_search, sync_replace)
    print("Arg parser updated inline.")
else:
    print("Could not find sync_search block in renderer.js.")

# We also need to capture JSON stdout for the analytics block.
# Look for data.toString() processing in activeProcess.stdout.on
stdout_search = """      // Process any json progress updates quietly
      const lines = data.toString().split('\\n');"""

stdout_replace = """      const lines = data.toString().split('\\n');
      for (const line of lines) {
         if (line.includes('SYNC_STATS:')) {
            try {
               const stats = JSON.parse(line.split('SYNC_STATS:')[1]);
               document.getElementById('sync-analytics-board').classList.remove('hidden');
               document.getElementById('sync-stat-rows').innerText = stats.total_rows.toLocaleString();
               
               const dropPercent = ((stats.dropped_rows / (stats.total_rows + stats.dropped_rows)) * 100).toFixed(1);
               document.getElementById('sync-stat-drops').innerText = dropPercent + "%";
               
               let classHtml = '';
               for (const [cls, count] of Object.entries(stats.classes)) {
                  classHtml += `<span class="badge bg-slate-800 border-emerald-500/30 text-[10px]">${cls}: ${count}</span>`;
               }
               document.getElementById('sync-stat-classes').innerHTML = classHtml;
            } catch(e) {}
         }
      }"""

if stdout_search in js:
    js = js.replace(stdout_search, stdout_replace)
    print("Stdout parser updated.")
else:
    # Relaxed search
    if "const lines = data.toString().split('\\n');" in js:
        js = js.replace("const lines = data.toString().split('\\n');", stdout_replace)
        print("Stdout parser updated via relaxed search.")
    else:
        print("Could not attach stdout parser.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("renderer.js updated successfully.")
