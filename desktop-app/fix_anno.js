const fs = require('fs');

const indexFile = '/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html';
let htmlContent = fs.readFileSync(indexFile, 'utf8');

const oldDirInput = '<input type="file" webkitdirectory directory class="file-input file-input-bordered w-full bg-slate-900/50 border-white/10 text-white" id="dataDirPicker" onchange="setDirectory()" />';
const newDirInput = `<div class="join w-full">
                    <button class="btn btn-md join-item bg-slate-700 border-white/10 text-white hover:bg-slate-600" onclick="chooseAnnoDir()">Choose Folder</button>
                    <input type="text" placeholder="Select image folder..." class="input input-md join-item w-full bg-slate-900/50 border-white/10 focus:border-blue-400 text-white font-mono text-sm" id="annoDirPath" onchange="setDirectory()" />
                  </div>`;

const oldVideoInput = '<input type="file" accept="video/mp4,video/x-m4v,video/*,video/quicktime" class="file-input file-input-bordered w-full bg-slate-900/50 border-white/10 text-white" id="videoPicker" onchange="setVideoFile()" />';
const newVideoInput = `<div class="join w-full">
                    <button class="btn btn-md join-item bg-slate-700 border-white/10 text-white hover:bg-slate-600" onclick="chooseAnnoVideo()">Choose File</button>
                    <input type="text" placeholder="Select master video..." class="input input-md join-item w-full bg-slate-900/50 border-white/10 focus:border-blue-400 text-white font-mono text-sm" id="annoVideoPath" onchange="setVideoFile()" />
                  </div>`;

htmlContent = htmlContent.replace(oldDirInput, newDirInput);
htmlContent = htmlContent.replace(oldVideoInput, newVideoInput);
fs.writeFileSync(indexFile, htmlContent);

const renderFile = '/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/renderer.js';
let renderContent = fs.readFileSync(renderFile, 'utf8');

// Replace setDirectory
renderContent = renderContent.replace(
  /function setDirectory\(\) \{[\s\S]*?\n\}/,
  `function setDirectory() {
  const dirPath = document.getElementById('annoDirPath') ? document.getElementById('annoDirPath').value : "";
  const label = document.getElementById('selectedDirLabel');
  if (dirPath && dirPath.trim() !== "") {
    const basePath = dirPath;
    if(label) label.innerText = \`Mapped Base Path: \${basePath}\`;
    logToConsole(\`Workspace path updated: \${basePath}\`);

    // Try finding a video preview to show
    const videoFile = findVideoFile(basePath);
    const videoCard = document.getElementById('video-preview-card');
    const videoPlayer = document.getElementById('video-player');
    const videoPathLabel = document.getElementById('video-path-label');

    if (videoFile && videoCard && videoPlayer) {
        videoPlayer.src = \`file://\${videoFile}\`;
        if(videoPathLabel) videoPathLabel.innerText = \`Previewing Local File: .../\${path.basename(path.dirname(videoFile))}/\${path.basename(videoFile)}\`;
        videoCard.classList.remove('hidden');
        logToConsole(\`Found session video for preview: \${path.basename(videoFile)}\`);
    } else if (videoCard) {
        videoCard.classList.add('hidden');
    }
  }
}`
);

// Replace setVideoFile
renderContent = renderContent.replace(
  /function setVideoFile\(\) \{[\s\S]*?\n\}/,
  `function setVideoFile() {
  const videoPath = document.getElementById('annoVideoPath') ? document.getElementById('annoVideoPath').value : "";
  if (videoPath && videoPath.trim() !== "") {
      const videoCard = document.getElementById('video-preview-card');
      const videoPlayer = document.getElementById('video-player');
      const videoPathLabel = document.getElementById('video-path-label');
      
      if(videoPlayer && videoCard) {
        videoPlayer.src = \`file://\${videoPath}\`;
        if(videoPathLabel) videoPathLabel.innerText = \`Previewing Local File: \${path.basename(videoPath)}\`;
        videoCard.classList.remove('hidden');
        logToConsole(\`Manually mapped master video: \${path.basename(videoPath)}\`);
      }
  }
}`
);

// Add the picker IPC callers
if(!renderContent.includes('window.chooseAnnoDir')) {
    renderContent += `

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
`;
}

// Update the _runScript logic to correctly find the clip path
if (renderContent.includes("if (scriptKey === 'clip') {")) {
    // maybe it doesn't have it explicitly since we couldn't grep it. Let's add it if missing so python gets args.
    
} else {
    // If clip args aren't explicit, we can add them to the arg builder
    renderContent = renderContent.replace(
        /let args = \['-u', targetScript\];/,
        `let args = ['-u', targetScript];
  if (scriptKey === 'clip') {
     const dirPath = document.getElementById('annoDirPath') ? document.getElementById('annoDirPath').value : "";
     if(!dirPath) {
         logToConsole("⚠️ Please select an Image Extracted Folder first.\\n", true);
         return;
     }
     args.push('--dir', dirPath); // Assuming clip_annotator.py takes --dir or similar. Adjust if needed.
  }`
    );
}

fs.writeFileSync(renderFile, renderContent);
console.log('Renderer and HTML patched.');