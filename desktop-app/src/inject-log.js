const fs = require('fs');
const path = require('path');
const logFile = path.join(__dirname, 'console.log');
fs.writeFileSync(logFile, '');
const oldLog = console.log;
const oldErr = console.error;
console.log = function(...args) { fs.appendFileSync(logFile, 'LOG: ' + args.join(' ') + '\n'); oldLog.apply(console, args); };
console.error = function(...args) { fs.appendFileSync(logFile, 'ERR: ' + args.join(' ') + '\n'); oldErr.apply(console, args); };
window.addEventListener("error", function(e) { fs.appendFileSync(logFile, "CAUGHT ERR: " + e.message + "\n"); });
