import re

js_path = 'desktop-app/src/renderer.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Remap the script path
js = js.replace("'clip': path.join(rootDir, 'data_pipeline/clip_auto_labeler.py')", "'clip': path.join(rootDir, 'data_pipeline/yolo_clip_auto.py')")


# 2. Modify the stop process helper if it doesn't already cover clip
stopClipProcess_code = """
window.stopClipProcess = function() {
    if (window.activeClipProcess) {
        window.activeClipProcess.kill();
        logToConsole(`\\n[System] Auto Annotation aborted safely.\\n`);
    }
}
"""
if "window.stopClipProcess" not in js:
    js += stopClipProcess_code

# 3. Add logic in runScript for "clip"
old_clip_block = """    if (scriptKey === 'clip') {
      const isSelectAll = document.getElementById('btn-select-all').checked;
      if (!isSelectAll) {
        // Collect checked boxes
        const container = document.getElementById('clip-classes-container');
        const checkboxes = container.querySelectorAll('input[type="checkbox"]:checked');
        const classes = Array.from(checkboxes).map(cb => cb.value);
        
        if (classes.length > 0) {
          args.push('--classes');
          args.push(...classes);
        } else {
          appendLog('❌ Error: No classes selected. Select at least one class to annotate.');
          spinner.classList.add('hidden');
          btn.disabled = false;
          return;
        }
      }
      
      const customOut = document.getElementById('clipCustomOutPath')?.value;
      if (customOut) args.push('--out', customOut);
    }"""

new_clip_block = """    if (scriptKey === 'clip') {
      const isSelectAll = document.getElementById('btn-select-all').checked;
      if (!isSelectAll) {
        const container = document.getElementById('clip-classes-container');
        const checkboxes = container.querySelectorAll('input[type="checkbox"]:checked');
        const classes = Array.from(checkboxes).map(cb => cb.value);
        
        if (classes.length > 0) {
          args.push('--classes');
          args.push(...classes);
        } else {
          appendLog('❌ Error: Select at least one YOLO target class.');
          spinner.classList.add('hidden');
          btn.disabled = false;
          return;
        }
      }
      
      const customOut = document.getElementById('clipCustomOutPath')?.value;
      if (customOut) args.push('--out', customOut);

      const doStageTwo = document.getElementById('toggle-two-stage')?.checked;
      if (doStageTwo) args.push('--use_clip');

      // Update UI 
      const stopBtn = document.getElementById('btn-clip-stop');
      if (stopBtn) stopBtn.classList.remove('hidden');
      const statsBoard = document.getElementById('auto-anno-stats');
      if (statsBoard) statsBoard.classList.remove('hidden');
    }"""

js = js.replace(old_clip_block, new_clip_block)


# 4. Handle process attachment
old_spawn = """    const pythonProcess = spawn(config.condaPython, args, {
      cwd: config.workspaceRoot
    });
    if (scriptKey === 'train') window.activeTrainingProcess = pythonProcess;
"""

new_spawn = """    const pythonProcess = spawn(config.condaPython, args, {
      cwd: config.workspaceRoot
    });
    if (scriptKey === 'train') window.activeTrainingProcess = pythonProcess;
    if (scriptKey === 'clip') window.activeClipProcess = pythonProcess;
"""
if "window.activeClipProcess = pythonProcess" not in js:
    js = js.replace(old_spawn, new_spawn)

# 5. Handle stdout to intercept CLIP JSON telemetry
parser_add = """
        // --- LIVE AUTO ANNOTATION STATS INTERCEPT ---
        if (scriptKey === 'clip' && strData.includes('ANNO_STATS:')) {
            const lines = strData.split('\\n');
            lines.forEach(l => {
                if (l.includes('ANNO_STATS:')) {
                    try {
                        const jsonStr = l.split('ANNO_STATS:')[1].trim();
                        const stats = JSON.parse(jsonStr);
                        
                        const fElem = document.getElementById('stat-anno-frames');
                        const oElem = document.getElementById('stat-anno-objects');
                        const eElem = document.getElementById('stat-anno-eta');
                        
                        if(fElem) fElem.innerText = stats.frame;
                        if(oElem) oElem.innerText = stats.objects;
                        if(eElem) eElem.innerText = stats.eta || '--:--';
                    } catch(e) {}
                }
            });
        }
"""
js = js.replace("// --- LIVE TRAIN STATS INTERCEPT ---", parser_add + "\n        // --- LIVE TRAIN STATS INTERCEPT ---")

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
print("JS UI auto patch updated successfully!")
