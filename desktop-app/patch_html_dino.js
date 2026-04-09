const fs = require('fs');
const file = 'src/index.html';
let content = fs.readFileSync(file, 'utf8');

const oldBtns = `              <!-- Action Buttons -->
              <div class="flex gap-4">
                <button class="btn border-0 bg-indigo-600 hover:bg-indigo-500 text-white px-8 h-12 shadow-indigo-900/30 flex-1 rounded-none" onclick="runScript('clip')" id="btn-clip">
                  <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
                  Initialize Hybrid Annotation
                  <span class="loading loading-spinner hidden w-4 h-4 ml-2" id="spinner-clip"></span>
                </button>
              </div>`;

const newBtns = `              <!-- Action Buttons -->
              <div class="flex gap-2">
                <button class="btn border-0 bg-indigo-600 hover:bg-indigo-500 text-white px-4 h-12 shadow-indigo-900/30 flex-1 rounded-none" onclick="runScript('clip')" id="btn-clip">
                  Fast YOLOv11 Annotation
                  <span class="loading loading-spinner hidden w-4 h-4 ml-2" id="spinner-clip"></span>
                </button>
                <button class="btn border-0 bg-cyan-600 hover:bg-cyan-500 text-white px-4 h-12 shadow-cyan-900/30 flex-1 rounded-none" onclick="runScript('dino')" id="btn-dino">
                  Grounding DINO (High Acc)
                  <span class="loading loading-spinner hidden w-4 h-4 ml-2" id="spinner-dino"></span>
                </button>
              </div>`;

content = content.replace(oldBtns, newBtns);
fs.writeFileSync(file, content);
console.log('index.html buttons patched');
