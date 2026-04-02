const fs = require('fs');
const file = '/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html';
let txt = fs.readFileSync(file, 'utf8');

const target = `<input type="text" placeholder="Defaults to ./VideoFrames if blank" class="input input-md w-full bg-slate-900/50 border-white/10 focus:border-blue-400 text-white font-mono text-sm" id="extractCustomOutPath" />`;

const replacement = `<div class="flex gap-2">
  <input type="text" placeholder="Defaults to ./VideoFrames if blank" class="input input-md w-full bg-slate-900/50 border-white/10 focus:border-blue-400 text-white font-mono text-sm" id="extractCustomOutPath" />
  <button class="btn btn-md bg-slate-800 text-white border-white/10 hover:bg-slate-700" onclick="chooseOutputDir()">Browse</button>
</div>`;

if (txt.includes(target)) {
    txt = txt.replace(target, replacement);
    fs.writeFileSync(file, txt);
    console.log("Replaced");
} else {
    console.log("Target not found");
}
