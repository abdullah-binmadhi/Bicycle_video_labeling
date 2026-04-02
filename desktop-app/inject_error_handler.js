const fs = require('fs');
const file = '/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/renderer.js';
let content = fs.readFileSync(file, 'utf8');

if (!content.includes('window.addEventListener("error"')) {
    const errorFix = `
window.addEventListener("error", (event) => {
    logToConsole("ERROR: " + event.message + "<br/>" + event.filename + ":" + event.lineno, true);
});
`;
    content = content + errorFix;
    fs.writeFileSync(file, content, 'utf8');
}
