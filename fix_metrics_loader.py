import re

with open('desktop-app/src/renderer.js', 'r') as f:
    text = f.read()

# Delete the file loading logic handling the deleted stats
metrics_regex = re.compile(r'window\.chooseMetricsFile = async function\(\) \{.*?\n\};\n', re.DOTALL)
safe_metrics = """window.chooseMetricsFile = async function() {
    const { ipcRenderer } = require('electron');
    const filePath = await ipcRenderer.invoke('dialog:openMetrics');
    if (filePath) {
        document.getElementById('analyticsFilePath').value = filePath;
        
        try {
            const fs = require('fs');
            const data = fs.readFileSync(filePath, 'utf-8');
            const metrics = JSON.parse(data);
            
            showToast('Metrics loaded & parsed successfully!', 'success');
        } catch (e) {
            console.error(e);
            showToast('Error reading metrics file.', 'error');
        }
    }
};
"""
text = metrics_regex.sub(safe_metrics, text)

with open('desktop-app/src/renderer.js', 'w') as f:
    f.write(text)

