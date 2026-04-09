const fs = require('fs');
const js = fs.readFileSync('desktop-app/src/renderer.js', 'utf8');
// try to parse
try { new Function(js); console.log("OK JS") } catch(e) { console.log(e); }
