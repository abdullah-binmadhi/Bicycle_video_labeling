with open("desktop-app/src/renderer.js", "r") as f:
    text = f.read()

func = """window.renderLegend = function() {
    const container = document.getElementById('dynamic-legend-controls');
    if (!container) return;
    
    // Unhide the parent container
    if (container.parentElement) {
        container.parentElement.classList.remove('hidden');
    }
    
    container.innerHTML = '';
"""

text = text.replace("window.renderLegend = function() {\n    const container = document.getElementById('dynamic-legend-controls');\n    if (!container) return;\n    container.innerHTML = '';", func)

with open("desktop-app/src/renderer.js", "w") as f:
    f.write(text)

print("patched")
