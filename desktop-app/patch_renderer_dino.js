const fs = require('fs');
const file = 'src/renderer.js';
let content = fs.readFileSync(file, 'utf8');

content = content.replace("if (scriptKey === 'clip') {", "if (scriptKey === 'clip' || scriptKey === 'dino') {");

const oldModelConf = `     const modelSelectEl = document.getElementById('clipModelSelect');
     if (modelSelectEl && modelSelectEl.value) {
         args.push('--model', modelSelectEl.value);
     }
     
     const confSliderEl = document.getElementById('clipConfSlider');
     if (confSliderEl && confSliderEl.value) {
         args.push('--conf', (parseFloat(confSliderEl.value) / 100).toFixed(2));
     }`;

const newModelConf = `     if (scriptKey === 'clip') {
         const modelSelectEl = document.getElementById('clipModelSelect');
         if (modelSelectEl && modelSelectEl.value) {
             args.push('--model', modelSelectEl.value);
         }
         const confSliderEl = document.getElementById('clipConfSlider');
         if (confSliderEl && confSliderEl.value) {
             args.push('--conf', (parseFloat(confSliderEl.value) / 100).toFixed(2));
         }
     } else if (scriptKey === 'dino') {
         args.push('--conf', '0.25'); 
         args.push('--text_conf', '0.25');
     }`;

content = content.replace(oldModelConf, newModelConf);

fs.writeFileSync(file, content);
console.log('renderer logic patched');
