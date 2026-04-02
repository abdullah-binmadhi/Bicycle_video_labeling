const fs = require('fs');
const file = '/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/renderer.js';
let txt = fs.readFileSync(file, 'utf8');

if (!txt.includes('previewExtractVideo')) {
    txt += `\n
window.previewExtractVideo = function() {
    const input = document.getElementById('extractVideoPicker');
    if (input.files.length > 0) {
        logToConsole("ℹ️ Selected Video: " + input.files[0].path);
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
`;
    fs.writeFileSync(file, txt);
}
