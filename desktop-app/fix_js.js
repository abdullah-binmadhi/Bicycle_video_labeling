const fs = require('fs');
const file = '/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/renderer.js';

let text = fs.readFileSync(file, 'utf8');

const sIdx = text.indexOf('function setProcessStatus(running, scriptKey) {');
const eIdx = text.indexOf('function _runScript(scriptKey) {');

if (sIdx !== -1 && eIdx !== -1) {
  const newText = `function setProcessStatus(running, scriptKey) {
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
    logToConsole("\\n⚠️ Stopping execution manually...\\n", true);
    activeProcess.kill("SIGINT");
    const prog = document.getElementById("extract-progress-container");
    if (prog) prog.classList.add("hidden");
  }
}

function runScript(scriptKey) {
  try {
    logToConsole("🟢 Starting script execution for: " + scriptKey);
    _runScript(scriptKey);
  } catch(e) {
    logToConsole("⚠️ App Error: " + e.toString() + "<br/>" + e.stack, true);
  }
}

`;
  
  text = text.substring(0, sIdx) + newText + text.substring(eIdx);
  fs.writeFileSync(file, text);
  console.log("Successfully fixed renderer.js");
} else {
  console.log("Could not find replacement indices", sIdx, eIdx);
}
