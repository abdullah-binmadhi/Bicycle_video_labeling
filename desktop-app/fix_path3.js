const fs = require('fs');
const filepath = '/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/renderer.js';
let content = fs.readFileSync(filepath, 'utf8');

content = content.replace(
  "PATH: '/opt/homebrew/bin:/usr/local/bin:/Library/Frameworks/Python.framework/Versions/3.14/bin:' + (process.env.PATH || '')",
  "PATH: (process.env.PATH || '') + ':/Library/Frameworks/Python.framework/Versions/3.14/bin:/opt/homebrew/bin:/usr/local/bin'"
);

fs.writeFileSync(filepath, content);
