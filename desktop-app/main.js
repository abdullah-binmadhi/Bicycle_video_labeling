const { app, BrowserWindow, ipcMain } = require('electron')
const path = require('path')

const createWindow = () => {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true, // For simplicity communicating to local python
      contextIsolation: false
    }
  })
  win.loadFile('src/index.html');
  win.webContents.openDevTools();
  win.webContents.on('console-message', (event, level, message, line, sourceId) => { require('fs').appendFileSync('/tmp/elec.log', message + '\n'); });

}


const { dialog } = require('electron');
ipcMain.handle('dialog:openFile', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [{ name: 'Movies', extensions: ['mkv', 'avi', 'mp4', 'mov', 'm4v', 'qt'] }]
  });
  if (canceled) { return null; } else { return filePaths[0]; }
});

ipcMain.handle('dialog:openDirectory', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openDirectory', 'createDirectory']
  });
  if (canceled) { return null; } else { return filePaths[0]; }
});

ipcMain.handle('dialog:openMetrics', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [{ name: 'Metrics Files', extensions: ['json', 'csv'] }]
  });
  if (canceled) return null;
  return filePaths[0];
});

ipcMain.handle('dialog:openCSV', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [{ name: 'CSV Files', extensions: ['csv'] }]
  });
  if (canceled) { return null; } else { return filePaths[0]; }
});

ipcMain.handle('dialog:saveCSV', async () => {
  const { canceled, filePath } = await dialog.showSaveDialog({
    title: 'Export GPS CSV',
    defaultPath: 'gps_classifications.csv',
    filters: [{ name: 'CSV Files', extensions: ['csv'] }]
  });
  if (canceled) { return null; } else { return filePath; }
});

ipcMain.handle('dialog:openModel', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [{ name: 'PyTorch Model', extensions: ['pth', 'pt'] }]
  });
  if (canceled) { return null; } else { return filePaths[0]; }
});

ipcMain.handle('dialog:openVideo', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [{ name: 'Video Files', extensions: ['mp4', 'mov', 'avi', 'mkv'] }]
  });
  if (canceled) { return null; } else { return filePaths[0]; }
});

app.whenReady().then(() => {
  createWindow()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

ipcMain.handle('read-dir-images', async (event, dirPath) => {
  try {
    const fs = require('fs');
    const path = require('path');
    const files = fs.readdirSync(dirPath);
    const images = files.filter(f => f.match(/\.(png|jpe?g|webp)$/i)).map(f => path.join(dirPath, f));
    return images;
  } catch (e) {
    return [];
  }
});

ipcMain.handle('save-annotated-image', async (event, srcPath, base64Data) => {
  try {
    const fs = require('fs');
    const base64DataObj = base64Data.replace(/^data:image\/jpeg;base64,/, "").replace(/^data:image\/png;base64,/, "");
    fs.writeFileSync(srcPath, base64DataObj, 'base64');
    return true;
  } catch (e) {
    return false;
  }
});
