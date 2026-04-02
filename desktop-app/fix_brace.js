const fs = require('fs');
let txt = fs.readFileSync('src/renderer.js', 'utf8');

const target = "if (!fs.existsSync(outDir)) { fs.mkdirSync(outDir, { recursive: true }); }\n    args.push('--video', videoPath);";
const replacement = "if (!fs.existsSync(outDir)) { fs.mkdirSync(outDir, { recursive: true }); }\n      }\n    args.push('--video', videoPath);";

txt = txt.replace(target, replacement);
fs.writeFileSync('src/renderer.js', txt);
