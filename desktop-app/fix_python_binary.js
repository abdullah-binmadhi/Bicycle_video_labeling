const fs = require('fs');
const filepath = '/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/renderer.js';
let content = fs.readFileSync(filepath, 'utf8');

// Replace the generic pythonPath definition with a smart resolving one
content = content.replace(
  "const pythonPath = 'python3';",
  `let pythonPath = 'python3';
const preferredPython = '/Library/Frameworks/Python.framework/Versions/3.14/bin/python3';
if (require('fs').existsSync(preferredPython)) {
    pythonPath = preferredPython;
}`
);

fs.writeFileSync(filepath, content);
