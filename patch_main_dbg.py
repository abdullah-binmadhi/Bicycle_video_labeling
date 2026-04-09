import sys
html = open("desktop-app/main.js", "r").read()
html = html.replace("win.webContents.openDevTools();", "win.webContents.openDevTools();\n  win.webContents.on('console-message', (event, level, message, line, sourceId) => { require('fs').appendFileSync('/tmp/elec.log', message + '\\n'); });\n")
open("desktop-app/main.js", "w").write(html)
