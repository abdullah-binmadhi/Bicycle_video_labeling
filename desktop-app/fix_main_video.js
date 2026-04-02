const fs = require('fs');
const filepath = '/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/main.js';
let content = fs.readFileSync(filepath, 'utf8');

if (!content.includes('dialog:openFile')) {
  content = content.replace(
    "ipcMain.handle('dialog:openDirectory'",
    `ipcMain.handle('dialog:openFile', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [{ name: 'Movies', extensions: ['mkv', 'avi', 'mp4', 'mov', 'm4v', 'qt'] }]
  });
  if (canceled) { return null; } else { return filePaths[0]; }
});

ipcMain.handle('dialog:openDirectory'`
  );
  fs.writeFileSync(filepath, content);
}
