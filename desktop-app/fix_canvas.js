const fs = require('fs');
const path = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/renderer.js";
let code = fs.readFileSync(path, 'utf8');

// Just make sure my previous fix is fine, and I'll add fillRect as well so the user gets "rich and contrasty".
let newCode = code.replace(
/for \(let p = 0; p < passes; p\+\+\) {\s*datasetContext\.strokeRect\(box\.x, box\.y, box\.w, box\.h\);\s*}/,
`for (let p = 0; p < passes; p++) {
                datasetContext.strokeRect(box.x, box.y, box.w, box.h);
            }
            
            // Fill inner box with a translucent version of the same color for richness
            datasetContext.globalAlpha = baseAlpha * 0.2;
            for (let p = 0; p < passes; p++) {
                datasetContext.fillRect(box.x, box.y, box.w, box.h);
            }`);

fs.writeFileSync(path, newCode);
console.log("Updated passes to include fillRect");
