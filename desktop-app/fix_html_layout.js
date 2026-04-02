const fs = require('fs');
const file = '/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html';
let txt = fs.readFileSync(file, 'utf8');

const targetRegex = /<div class="flex flex-col">\s*<label class="text-xs uppercase tracking-widest font-bold text-slate-400 mb-2">Custom Output Path \(Optional\)<\/label>[\s\S]*?<\/div>(\s*<\/div>)*\s*<p class="text-xs text-slate-500 mt-2">Required if the original/m;

const replacement = `<div class="flex flex-col">
                  <label class="text-xs uppercase tracking-widest font-bold text-slate-400 mb-2">Custom Output Path (Optional)</label>
                  <div class="join w-full">
                    <button class="btn btn-md join-item bg-slate-700 border-white/10 text-white hover:bg-slate-600" onclick="chooseOutputDir()">Choose Path</button>
                    <input type="text" placeholder="Defaults to ./VideoFrames if blank" class="input input-md join-item w-full bg-slate-900/50 border-white/10 focus:border-blue-400 text-white font-mono text-sm" id="extractCustomOutPath" />
                  </div>
                </div>
              <p class="text-xs text-slate-500 mt-2">Required if the original`;

if (txt.match(targetRegex)) {
    txt = txt.replace(targetRegex, replacement);
    fs.writeFileSync(file, txt);
    console.log("HTML replaced successfully!");
} else {
    // If exact regex fails, do a more brutal substring replacement just in case
    console.log("Regex fell through, searching manually...");
    const startStr = '<label class="text-xs uppercase tracking-widest font-bold text-slate-400 mb-2">Custom Output Path (Optional)</label>';
    const endStr = '<p class="text-xs text-slate-500 mt-2">Required if the original';
    
    let sIdx = txt.indexOf(startStr);
    let eIdx = txt.indexOf(endStr);
    if(sIdx !== -1 && eIdx !== -1) {
        // Back up to the <div class="flex flex-col">
        const prefix = txt.substring(0, sIdx);
        sIdx = prefix.lastIndexOf('<div class="flex flex-col">');
        
        txt = txt.substring(0, sIdx) + replacement + txt.substring(eIdx + endStr.length);
        fs.writeFileSync(file, txt);
        console.log("HTML replaced via fallback manual search.");
    } else {
        console.log("Could not find the target code in index.html");
    }
}
