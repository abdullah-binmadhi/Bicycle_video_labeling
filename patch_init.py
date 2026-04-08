with open('desktop-app/src/renderer.js', 'r') as f:
    content = f.read()

old_str = """
    } else if (analyticsMap) {
        setTimeout(() => analyticsMap.invalidateSize(), 300);
    }
}
"""

new_str = """
    } else if (analyticsMap) {
        setTimeout(() => analyticsMap.invalidateSize(), 300);
    }
    
    // Ensure charts start in their unticked states (empty or correct visual)
    if (typeof window.updateTrainingCharts === 'function') {
        window.updateTrainingCharts();
    }
    if (typeof window.updateMapState === 'function') {
        window.updateMapState();
    }
}
"""

if old_str in content:
    content = content.replace(old_str, new_str)
    with open('desktop-app/src/renderer.js', 'w') as f:
        f.write(content)
    print("Fixed initialization.")
else:
    print("Could not find old_str")
