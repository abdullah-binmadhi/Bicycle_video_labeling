const fs = require('fs');
const filepath = '/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/renderer.js';
let content = fs.readFileSync(filepath, 'utf8');

content = content.replace(
  "  const cwdPath = path.join(__dirname, '../../');\n  \n  activeProcess = spawn(pythonPath, args, { cwd: cwdPath });",
  `  const cwdPath = path.join(__dirname, '../../');
  
  // Inject common macOS paths so packaged Electron apps can find python3
  const customEnv = Object.assign({}, process.env, {
    PATH: '/opt/homebrew/bin:/usr/local/bin:/Library/Frameworks/Python.framework/Versions/3.14/bin:' + (process.env.PATH || '')
  });
  
  activeProcess = spawn(pythonPath, args, { cwd: cwdPath, env: customEnv });`
);

fs.writeFileSync(filepath, content);
