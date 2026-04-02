import os

html_file = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html"
with open(html_file, 'r', encoding='utf-8') as f:
    html_content = f.read()

# 1. Add "Abort" button next to status-badge
abort_button = '''
        <button id="btn-abort" class="btn btn-error btn-sm hidden drop-shadow-md text-white font-bold mr-2" onclick="killProcess()">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clip-rule="evenodd" /></svg>
          Abort Process
        </button>
        <span class="badge badge-success badge-sm py-3 px-3 gap-2 bg-success/20 text-success border-0" id="status-badge">'''

html_content = html_content.replace('<span class="badge badge-success badge-sm py-3 px-3 gap-2 bg-success/20 text-success border-0" id="status-badge">', abort_button)

with open(html_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("HTML modified for Abort button.")

js_file = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/renderer.js"
with open(js_file, 'r', encoding='utf-8') as f:
    js_content = f.read()

# 2. Add process state for visibility of Abort button
set_process_status_old = """    statusText.innerText = `Running ${scriptKey}...`;
    document.getElementById('status-badge').classList.replace('badge-success', 'badge-warning');
  } else {"""

set_process_status_new = """    statusText.innerText = `Running ${scriptKey}...`;
    document.getElementById('status-badge').classList.replace('badge-success', 'badge-warning');
    if(document.getElementById('btn-abort')) document.getElementById('btn-abort').classList.remove('hidden');
  } else {"""
js_content = js_content.replace(set_process_status_old, set_process_status_new)

set_process_status_idle_old = """    statusText.innerText = 'Ready';
    document.getElementById('status-badge').classList.replace('badge-warning', 'badge-success');
  }"""

set_process_status_idle_new = """    statusText.innerText = 'Ready';
    document.getElementById('status-badge').classList.replace('badge-warning', 'badge-success');
    if(document.getElementById('btn-abort')) document.getElementById('btn-abort').classList.add('hidden');
  }"""
js_content = js_content.replace(set_process_status_idle_old, set_process_status_idle_new)

# 3. Add killProcess and persistent settings functions
extra_js = """

// --- ADVANCED FEATURES ---

// KILL PROCESS
window.killProcess = function() {
  if (activeProcess) {
    logToConsole('\\n[System] Sending INTERRUPT signal to abort process...\\n', true);
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
  logToConsole('[System] Settings saved to local cache.\\n');
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
"""

if "// KILL PROCESS" not in js_content:
    js_content += extra_js

with open(js_file, 'w', encoding='utf-8') as f:
    f.write(js_content)

print("JS modified for Abort button and Persistent Settings.")
