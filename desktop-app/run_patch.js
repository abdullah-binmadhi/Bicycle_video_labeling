const fs = require('fs');
const indexFile = '/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html';
let htmlContent = fs.readFileSync(indexFile, 'utf8');

const oldInputHtml = `<input type="file" accept="video/mp4,video/x-m4v,video/*,video/quicktime" class="file-input file-input-bordered file-input-md w-full bg-slate-900/50 border-white/10 text-white" id="extractVideoPicker" onchange="previewExtractVideo()" />`;

const newInputHtml = `<div class="join w-full">
                    <button class="btn btn-md join-item bg-slate-700 border-white/10 text-white hover:bg-slate-600" onclick="chooseVideoFile()">Choose File</button>
                    <input type="text" placeholder="Select video file..." class="input input-md join-item w-full bg-slate-900/50 border-white/10 focus:border-blue-400 text-white font-mono text-sm" id="extractVideoPath" onchange="previewExtractVideo()" />
                  </div>`;

if (htmlContent.includes('extractVideoPicker')) {
    htmlContent = htmlContent.replace(oldInputHtml, newInputHtml);
    fs.writeFileSync(indexFile, htmlContent);
}

const renderFile = '/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/renderer.js';
let renderContent = fs.readFileSync(renderFile, 'utf8');

if (!renderContent.includes('window.chooseVideoFile')) {
    const outputDirFuncText = "window.chooseOutputDir = async function() {\n    const { ipcRenderer } = require('electron');\n    const path = await ipcRenderer.invoke('dialog:openDirectory');\n    if (path) {\n        document.getElementById('extractCustomOutPath').value = path;\n        logToConsole(\"ℹ️ Selected Output Directory: \" + path);\n    }\n};";

    const videoFileFuncText = "\n\nwindow.chooseVideoFile = async function() {\n    const { ipcRenderer } = require('electron');\n    const path = await ipcRenderer.invoke('dialog:openFile');\n    if (path) {\n        document.getElementById('extractVideoPath').value = path;\n        logToConsole(\"ℹ️ Selected Video File: \" + path);\n        previewExtractVideo();\n    }\n};";

    renderContent = renderContent.replace(outputDirFuncText, outputDirFuncText + videoFileFuncText);
}

const oldExtractLogic = `const vidPicker = document.getElementById('extractVideoPicker');
      const customOutPath = document.getElementById('extractCustomOutPath') ? document.getElementById('extractCustomOutPath').value.trim() : "";
      const startTimeEl = document.getElementById('extractStartTime');
      const startTimeOverride = startTimeEl ? startTimeEl.value : "";
      
      if (!vidPicker || vidPicker.files.length === 0) {
        logToConsole("⚠️ Please select a video file to extract frames from.\\n", true);
        return;
      }
      const videoPath = vidPicker.files[0].path;`;

const newExtractLogic = `const extractVideoPathValue = document.getElementById('extractVideoPath') ? document.getElementById('extractVideoPath').value.trim() : "";
      const customOutPath = document.getElementById('extractCustomOutPath') ? document.getElementById('extractCustomOutPath').value.trim() : "";
      const startTimeEl = document.getElementById('extractStartTime');
      const startTimeOverride = startTimeEl ? startTimeEl.value : "";
      
      if (!extractVideoPathValue) {
        logToConsole("⚠️ Please select a video file to extract frames from.\\n", true);
        return;
      }
      const videoPath = extractVideoPathValue;`;

if (renderContent.includes("document.getElementById('extractVideoPicker')")) {
  renderContent = renderContent.replace(oldExtractLogic, newExtractLogic);
}

if (renderContent.includes("const file = vidPicker.files[0];")) {
  renderContent = renderContent.replace(
      "const vidPicker = document.getElementById('extractVideoPicker');\n  const previewPlayer = document.getElementById('extractPreview');\n\n  if (vidPicker.files && vidPicker.files.length > 0) {\n    const file = vidPicker.files[0];\n    const videoURL = URL.createObjectURL(file);\n    previewPlayer.src = videoURL;\n    previewPlayer.load();",
      "const vidPickerPath = document.getElementById('extractVideoPath') ? document.getElementById('extractVideoPath').value : '';\n  const previewPlayer = document.getElementById('extractPreview');\n\n  if (vidPickerPath) {\n    previewPlayer.src = 'file://' + vidPickerPath;\n    previewPlayer.load();"
  );
}

fs.writeFileSync(renderFile, renderContent);
console.log('Patched');
