const fs = require('fs');

// Patch main.js
let mainCode = fs.readFileSync('desktop-app/main.js', 'utf8');
if (!mainCode.includes('overwrite-master-annotations')) {
    const mainInjection = `
ipcMain.handle('overwrite-master-annotations', async (event, payload) => {
  try {
    const fs = require('fs');
    const path = require('path');
    
    const outputDir = payload.masterDir || path.join(__dirname, '../../');
    const csvPath = path.join(outputDir, 'master_annotations.csv');
    const schemaHeader = "image_id,label_code,class_name,xmin,ymin,xmax,ymax,score\\n";

    if (!fs.existsSync(csvPath)) {
        fs.writeFileSync(csvPath, schemaHeader, 'utf8');
    }

    const lines = fs.readFileSync(csvPath, 'utf8').split('\\n');
    const newLines = [];
    
    for (let i = 0; i < lines.length; i++) {
        if (lines[i].trim() === '') continue;
        if (i === 0) {
            newLines.push(lines[i]); 
            continue;
        }
        const cols = lines[i].split(',');
        if (cols[0] !== payload.image_id) {
            newLines.push(lines[i]);
        }
    }
    
    for (const ann of payload.annotations) {
        let rawLabel = (ann.class_name || "unknown").toLowerCase().trim();
        rawLabel = rawLabel.replace(/^\\d+\\s*-\\s*/, '');
        let label_code = ALLOWED_LABELS[rawLabel] || "0";
        
        const [xmin, ymin, xmax, ymax] = ann.bbox;
        const row = \`\${payload.image_id},\${label_code},\${rawLabel},\${xmin},\${ymin},\${xmax},\${ymax},\${ann.score}\`;
        newLines.push(row);
    }
    
    fs.writeFileSync(csvPath, newLines.join('\\n') + '\\n', 'utf8');
    return true;
  } catch (e) {
    console.error("Overwrite Annotation Error:", e);
    return false;
  }
});
`;
    mainCode = mainCode.replace("ipcMain.handle('save-master-annotation', async (event, payload) => {", mainInjection + "\nipcMain.handle('save-master-annotation', async (event, payload) => {");
    fs.writeFileSync('desktop-app/main.js', mainCode, 'utf8');
    console.log('main.js patched');
}

// Patch renderer.js
let renCode = fs.readFileSync('desktop-app/src/renderer.js', 'utf8');
const oldRenFunc = `    btnDatasetSave.addEventListener('click', async () => {
        if (currentDatasetImages.length === 0) return;
        if (currentBoxes.length === 0) {
            showToast('No boxes to save. Draw at least one bounding box.', 'error');
            return;
        }

        const imagePath = currentDatasetImages[currentDatasetIndex];
        const imageDir = require('path').dirname(imagePath);
        let savedCount = 0;

        for (const box of currentBoxes) {
            // Convert canvas display coordinates to xmin,ymin,xmax,ymax
            // Canvas dimensions match the display image - scale to image pixel space
            const imgW = datasetPreviewImg.naturalWidth || datasetPreviewImg.clientWidth;
            const imgH = datasetPreviewImg.naturalHeight || datasetPreviewImg.clientHeight;
            const scaleX = imgW / datasetAnnotationCanvas.width;
            const scaleY = imgH / datasetAnnotationCanvas.height;

            const xmin = Math.round(box.x * scaleX);
            const ymin = Math.round(box.y * scaleY);
            const xmax = Math.round((box.x + box.w) * scaleX);
            const ymax = Math.round((box.y + box.h) * scaleY);

            const ok = await ipcRenderer.invoke('save-master-annotation', {
                image_id: imagePath,
                class_name: box.label || 'unknown',
                score: 1.0,
                bbox: [xmin, ymin, xmax, ymax],
                masterDir: imageDir
            });
            if (ok) savedCount++;
        }

        if (savedCount === currentBoxes.length) {
            logToConsole(\`[Dataset Gallery] Saved \${savedCount} annotation(s) for: \${imagePath}\`);
            showToast('Saved frame to master dataset', 'success');
            
            // Advance to next
            if (currentDatasetIndex < currentDatasetImages.length - 1) {
                currentDatasetIndex++;
                loadDatasetImage(currentDatasetIndex);
            }
        } else {
            showToast('Failed to save annotations. Check console.', 'error');
        }
    });`;

const newRenFunc = `    btnDatasetSave.addEventListener('click', async () => {
        if (currentDatasetImages.length === 0) return;
        
        const imagePath = currentDatasetImages[currentDatasetIndex];
        const imageDir = require('path').dirname(imagePath);
        
        const annotations = [];

        for (const box of currentBoxes) {
            const imgW = datasetPreviewImg.naturalWidth || datasetPreviewImg.clientWidth;
            const imgH = datasetPreviewImg.naturalHeight || datasetPreviewImg.clientHeight;
            const scaleX = imgW / datasetAnnotationCanvas.width;
            const scaleY = imgH / datasetAnnotationCanvas.height;

            const xmin = Math.round(box.x * scaleX);
            const ymin = Math.round(box.y * scaleY);
            const xmax = Math.round((box.x + box.w) * scaleX);
            const ymax = Math.round((box.y + box.h) * scaleY);

            annotations.push({
                class_name: box.label || 'unknown',
                score: 1.0,
                bbox: [xmin, ymin, xmax, ymax]
            });
        }
        
        const ok = await ipcRenderer.invoke('overwrite-master-annotations', {
            image_id: imagePath,
            annotations: annotations,
            masterDir: imageDir
        });
        
        if (ok) {
            logToConsole(\`[Dataset Gallery] Saved \${annotations.length} annotation(s) for: \${imagePath}\`);
            showToast(\`Overwritten frame with \${annotations.length} boxes\`, 'success');
            
            if (currentDatasetIndex < currentDatasetImages.length - 1) {
                currentDatasetIndex++;
                loadDatasetImage(currentDatasetIndex);
            }
        } else {
            showToast('Failed to save annotations. Check console.', 'error');
        }
    });`;

if (renCode.includes(oldRenFunc)) {
    renCode = renCode.replace(oldRenFunc, newRenFunc);
    fs.writeFileSync('desktop-app/src/renderer.js', renCode, 'utf8');
    console.log('renderer.js patched');
} else {
    console.log('renderer.js could not be patched - string not found');
}
