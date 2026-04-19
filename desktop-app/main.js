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

// Full label dictionary matching the 135-class gallery dropdown (index.html)
// Keys match the raw value strings from <option value="..."> lowercased and stripped of numeric prefix
const ALLOWED_LABELS = {
    // Objects & Road Users
    "bicycle": "1",
    "potholes": "2",
    "manhole": "3",
    "water_puddle": "4",
    "uneven_surface": "5",
    "speed_bump": "6",
    "drain": "7",
    "crack": "8",
    "gravel": "9",
    "sand": "10",
    "mud": "11",
    "wet_leaves": "12",
    "dry_leaves": "13",
    "branches": "14",
    "ice": "15",
    "snow": "16",
    "glass": "17",
    "metal_plate": "18",
    "rail_tracks": "19",
    "cobblestone": "20",
    "brick_paving": "21",
    "concrete_pavers": "22",
    "tree_root": "23",
    "painted_lines": "24",
    "road_marking": "25",
    "crosswalk": "26",
    "pedestrian": "27",
    "dog": "28",
    "cat": "29",
    "squirrel": "30",
    "car": "31",
    "motorcycle": "32",
    "truck": "33",
    "bus": "34",
    "scooter": "35",
    "e-scooter": "36",
    "traffic_cone": "37",
    "bollard": "38",
    "construction_barrier": "39",
    "fallen_tree": "40",
    "debris": "41",
    "plastic_bag": "42",
    "trash_can": "43",
    "standing_water": "44",
    "oil_spill": "45",
    "smooth_asphalt": "46",
    "rough_asphalt": "47",
    "grate": "48",
    "tactile_paving": "49",
    "curb": "50",
    "shadow": "51",
    "street_light": "52",
    "traffic_light": "53",
    "stop_sign": "54",
    "yield_sign": "55",
    "speed_limit_sign": "56",
    "bus_stop": "57",
    "train_station": "58",
    "parked_car": "59",
    "moving_car": "60",
    "turning_car": "61",
    "reversing_car": "62",
    "emergency_vehicle": "63",
    "construction_vehicle": "64",
    "farm_vehicle": "65",
    "delivery_truck": "66",
    "garbage_truck": "67",
    "street_sweeper": "68",
    "snow_plow": "69",
    "tow_truck": "70",
    "flatbed_truck": "71",
    "semi_truck": "72",
    "box_truck": "73",
    "pickup_truck": "74",
    "van": "75",
    "minivan": "76",
    "suv": "77",
    "jeep": "78",
    "crossover": "79",
    "sedan": "80",
    "coupe": "81",
    "convertible": "82",
    "hatchback": "83",
    "station_wagon": "84",
    "sports_car": "85",
    "luxury_car": "86",
    "classic_car": "87",
    "antique_car": "88",
    "muscle_car": "89",
    "electric_car": "90",
    "hybrid_car": "91",
    "diesel_car": "92",
    "gas_car": "93",
    "hydrogen_car": "94",
    "fuel_cell_car": "95",
    "solar_car": "96",
    "flying_car": "97",
    "hover_car": "98",
    "submarine_car": "99",
    "boat_car": "100",
    "dirt_road": "101",
    "macadam": "102",
    "grassy_path": "103",
    "wood_planks": "104",
    "metal_grating": "105",
    "paved_path": "106",
    "unpaved_path": "107",
    "pothole_cluster": "108",
    "alligator_cracking": "109",
    "longitudinal_cracks": "110",
    "transverse_cracks": "111",
    "block_cracking": "112",
    "edge_cracking": "113",
    "rutting": "114",
    "shoving": "115",
    "corrugation": "116",
    "bleeding": "117",
    "polished_aggregate": "118",
    "pumping": "119",
    "raveling": "120",
    "stripping": "121",
    "delamination": "122",
    "patch": "123",
    "traverse_speed_bump": "124",
    "rubber_speed_bump": "125",
    "concrete_speed_bump": "126",
    "asphalt_speed_bump": "127",
    "wide_speed_bump": "128",
    "narrow_speed_bump": "129",
    "rumble_strips": "130",
    "speed_cushion": "131",
    "speed_table": "132",
    "bicycle_lane": "133",
    "bicycle_lane": "134",
    "asphalt": "135"
};

ipcMain.handle('save-master-annotation', async (event, payload) => {
  try {
    const fs = require('fs');
    const path = require('path');
    
    // Fallback dictionary retrieval or '0' for unknown
    let rawLabel = (payload.class_name || "unknown").toLowerCase().trim();
    // remove numeric prefixes from dropdowns if any (e.g. "3 - car" -> "car")
    rawLabel = rawLabel.replace(/^\d+\s*-\s*/, '');
    let label_code = ALLOWED_LABELS[rawLabel] || "0"; 

    const outputDir = payload.masterDir || path.join(__dirname, '../../');
    const csvPath = path.join(outputDir, 'master_annotations.csv');
    
    // image_id, label_code, class_name, xmin, ymin, xmax, ymax, score
    const schemaHeader = "image_id,label_code,class_name,xmin,ymin,xmax,ymax,score\n";
    
    if (!fs.existsSync(csvPath)) {
        fs.writeFileSync(csvPath, schemaHeader, 'utf8');
    }
    
    const [xmin, ymin, xmax, ymax] = payload.bbox;
    const row = `${payload.image_id},${label_code},${rawLabel},${xmin},${ymin},${xmax},${ymax},${payload.score}\n`;
    
    fs.appendFileSync(csvPath, row, 'utf8');
    return true;
  } catch (e) {
    console.error("Master Annotation Error:", e);
    return false;
  }
});
