const fs = require('fs');
const file = '/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/main.js';
let content = fs.readFileSync(file, 'utf8');

if (!content.includes('dialog:openDirectory')) {
    const dialogInject = `
const { dialog } = require('electron');
ipcMain.handle('dialog:openDirectory', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openDirectory', 'createDirectory']
  });
  if (canceled) { return null; } else { return filePaths[0]; }
});
`;
    content = content.replace("app.whenReady().then(() => {", dialogInject + "\napp.whenReady().then(() => {");
    fs.writeFileSync(file, content);
}
