const fs = require('fs');
const filepath = '/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/renderer.js';
let content = fs.readFileSync(filepath, 'utf8');

content = content.replace(
  /const cwdPath = path\.dirname\(targetScript\);\n\s*logToConsole\(`ℹ️ Working directory: \$\{cwdPath\}\\n`\);\n\n\s*activeProcess = spawn\(pythonPath, args, \{ cwd: cwdPath \}\);/g,
  `const cwdPath = path.dirname(targetScript);
  logToConsole(\`ℹ️ Working directory: \${cwdPath}\\n\`);

  const customEnv = Object.assign({}, process.env, {
    PATH: '/opt/homebrew/bin:/usr/local/bin:/Library/Frameworks/Python.framework/Versions/3.14/bin:' + (process.env.PATH || '')
  });
  
  activeProcess = spawn(pythonPath, args, { cwd: cwdPath, env: customEnv });`
);

fs.writeFileSync(filepath, content);
