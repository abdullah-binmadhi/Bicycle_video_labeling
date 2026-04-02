const fs = require('fs');
const renderFile = '/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/renderer.js';
let renderContent = fs.readFileSync(renderFile, 'utf8');

// Replace extract logic
renderContent = renderContent.replace(
  /const vidPicker = document\.getElementById\('extractVideoPicker'\);[\s\S]*?const videoPath = vidPicker\.files\[0\]\.path;/g,
  `const extractVideoPathValue = document.getElementById('extractVideoPath') ? document.getElementById('extractVideoPath').value.trim() : "";
      const customOutPath = document.getElementById('extractCustomOutPath') ? document.getElementById('extractCustomOutPath').value.trim() : "";
      const startTimeEl = document.getElementById('extractStartTime');
      const startTimeOverride = startTimeEl ? startTimeEl.value : "";
      
      if (!extractVideoPathValue) {
        logToConsole("⚠️ Please select a video file to extract frames from.\\n", true);
        return;
      }
      const videoPath = extractVideoPathValue;`
);

// Replace previewExtractVideo logic
renderContent = renderContent.replace(
  /window\.previewExtractVideo = function\(\) \{[\s\S]*?\};/g,
  `window.previewExtractVideo = function() {
    const inputPath = document.getElementById('extractVideoPath') ? document.getElementById('extractVideoPath').value : "";
    if (inputPath) {
        logToConsole("ℹ️ Validated Video ready to map: " + inputPath);
    }
};`
);

fs.writeFileSync(renderFile, renderContent);
console.log("Renderer.js completely scrubbed of old extractVideoPicker.");
