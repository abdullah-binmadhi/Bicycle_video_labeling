const fs = require('fs');
const p = 'renderer.js';

let code = `
// Auto-Generated Dataset Review Logic
let currentDatasetImages = [];
let currentDatasetIndex = 0;
let isDrawingDataset = false;
let datasetStartX = 0;
let datasetStartY = 0;

function setupDatasetGallery() {
    const btnUploadAutoDataset = document.getElementById('btn-upload-auto-dataset');
    const datasetPathLabel = document.getElementById('dataset-path-label');
    const datasetGalleryView = document.getElementById('dataset-gallery-view');
    const datasetPreviewImg = document.getElementById('dataset-preview-img');
    const datasetAnnotationCanvas = document.getElementById('dataset-annotation-canvas');
    const btnDatasetPrev = document.getElementById('btn-dataset-prev');
    const btnDatasetNext = document.getElementById('btn-dataset-next');
    const datasetCounter = document.getElementById('dataset-counter');
    const btnDatasetSave = document.getElementById('btn-dataset-save');
    const btnToolClear = document.getElementById('btn-tool-clear');

    if (!btnUploadAutoDataset || !datasetAnnotationCanvas) return;

    let datasetContext = datasetAnnotationCanvas.getContext('2d');

    function loadDatasetImage(index) {
        if (index >= 0 && index < currentDatasetImages.length) {
            datasetPreviewImg.src = "file://" + currentDatasetImages[index];
            datasetCounter.innerText = (index + 1) + " / " + currentDatasetImages.length;
            
            if (datasetAnnotationCanvas.width > 0) {
                datasetContext.clearRect(0, 0, datasetAnnotationCanvas.width, datasetAnnotationCanvas.height);
            }
        }
    }

    datasetPreviewImg.onload = () => {
        datasetAnnotationCanvas.width = datasetPreviewImg.clientWidth;
        datasetAnnotationCanvas.height = datasetPreviewImg.clientHeight;
    };

    btnUploadAutoDataset.addEventListener('click', async () => {
        const folderPath = await window.electronAPI.openDirectory();
        if (folderPath) {
            datasetPathLabel.innerText = folderPath;
            currentDatasetImages = await window.electronAPI.readDirImages(folderPath);
            if (currentDatasetImages && currentDatasetImages.length > 0) {
                currentDatasetIndex = 0;
                datasetGalleryView.classList.remove('hidden');
                loadDatasetImage(currentDatasetIndex);
            } else {
                if(typeof updateLog === 'function') updateLog("[WARN] No images found");
            }
        }
    });

    btnDatasetPrev.addEventListener('click', () => {
        if (currentDatasetIndex > 0) {
            currentDatasetIndex--;
            loadDatasetImage(currentDatasetIndex);
        }
    });

    btnDatasetNext.addEventListener('click', () => {
        if (currentDatasetIndex < currentDatasetImages.length - 1) {
            currentDatasetIndex++;
            loadDatasetImage(currentDatasetIndex);
        }
    });

    btnDatasetSave.addEventListener('click', async () => {
        if (currentDatasetImages.length === 0) return;
        
        const offscreen = document.createElement('canvas');
        offscreen.width = datasetPreviewImg.clientWidth;
        offscreen.height = datasetPreviewImg.clientHeight;
        const ctx = offscreen.getContext('2d');
        
        ctx.drawImage(datasetPreviewImg, 0, 0, offscreen.width, offscreen.height);
        ctx.drawImage(datasetAnnotationCanvas, 0, 0);

        const dataUrl = offscreen.toDataURL('image/jpeg', 1.0);
        const success = await window.electronAPI.saveAnnotatedImage(currentDatasetImages[currentDatasetIndex], dataUrl);
        if (success) {
            if(typeof updateLog === 'function') updateLog("[SUCCESS] Saved frame: " + currentDatasetImages[currentDatasetIndex]);
            btnDatasetSave.innerHTML = "SAVED!";
            setTimeout(() => btnDatasetSave.innerHTML = "[SAVE] Overwrite Frame", 1500);
        }
    });

    btnToolClear.addEventListener('click', () => {
        datasetContext.clearRect(0, 0, datasetAnnotationCanvas.width, datasetAnnotationCanvas.height);
    });

    datasetAnnotationCanvas.addEventListener('mousedown', (e) => {
        isDrawingDataset = true;
        const rect = datasetAnnotationCanvas.getBoundingClientRect();
        datasetStartX = e.clientX - rect.left;
        datasetStartY = e.clientY - rect.top;
    });

    datasetAnnotationCanvas.addEventListener('mousemove', (e) => {
        if (!isDrawingDataset) return;
        const rect = datasetAnnotationCanvas.getBoundingClientRect();
        const currentX = e.clientX - rect.left;
        const currentY = e.clientY - rect.top;
        
        datasetContext.clearRect(0, 0, datasetAnnotationCanvas.width, datasetAnnotationCanvas.height);
        datasetContext.strokeStyle = '#e0e0e0';
        datasetContext.lineWidth = 2;
        datasetContext.strokeRect(datasetStartX, datasetStartY, currentX - datasetStartX, currentY - datasetStartY);
    });

    datasetAnnotationCanvas.addEventListener('mouseup', () => {
        isDrawingDataset = false;
    });
}
document.addEventListener('DOMContentLoaded', setupDatasetGallery);
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setupDatasetGallery();
}
`;

fs.appendFileSync(p, '\n' + code);
console.log('Appended successfully');
