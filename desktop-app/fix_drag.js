const fs = require('fs');
const path = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/renderer.js";
let code = fs.readFileSync(path, 'utf8');

let newCode = code.replace(
/for \(let p = 0; p < dragPasses; p\+\+\) {\s*datasetContext\.strokeRect\(datasetStartX, datasetStartY, currentX \- datasetStartX, currentY \- datasetStartY\);\s*}/,
`for (let p = 0; p < dragPasses; p++) {
                datasetContext.strokeRect(datasetStartX, datasetStartY, currentX - datasetStartX, currentY - datasetStartY);
            }
            
            datasetContext.globalAlpha = dragBaseAlpha * 0.2;
            for (let p = 0; p < dragPasses; p++) {
                datasetContext.fillRect(datasetStartX, datasetStartY, currentX - datasetStartX, currentY - datasetStartY);
            }`);

fs.writeFileSync(path, newCode);
console.log("Updated drag box to include fillRect");
