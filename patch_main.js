const fs = require('fs');
let code = fs.readFileSync('desktop-app/main.js', 'utf8');
code = code.replace(
  "win.loadFile('src/index.html')",
  "win.loadFile('src/index.html'); win.webContents.on('console-message', (event, level, message, line, sourceId) => { require('fs').appendFileSync('renderer-console.log', message + '\\n'); }); win.webContents.on('did-fail-load', (e) => require('fs').appendFileSync('renderer-console.log', 'FAIL LOAD\\n')); win.webContents.on('render-process-gone', (e) => require('fs').appendFileSync('renderer-console.log', 'GONE\\n'));"
);
fs.writeFileSync('desktop-app/main.js', code);
