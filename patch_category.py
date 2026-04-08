import re

with open('desktop-app/src/renderer.js', 'r', encoding='utf-8') as f:
    content = f.read()

old_getCategory = '''window.getCategory = function(className) {
    const sLow = className.toLowerCase();
    if (sLow.includes('asphalt') || sLow.includes('gravel') || sLow.includes('cobble') || sLow.includes('134') || sLow.includes('8') || sLow.includes('19')) return 'Surfaces';
    if (sLow.includes('bicycle') || sLow.includes('rail') || sLow.includes('track') || sLow.includes('133') || sLow.includes('18')) return 'Infrastructure';
    if (sLow.includes('pothole') || sLow.includes('bump') || sLow.includes('1') || sLow.includes('5') || sLow.includes('crack')) return 'Anomalies';
    return 'Other';
};'''

new_getCategory = '''window.getCategory = function(className) {
    const surface_ids = [45, 46, 134, 8, 19, 20, 21, 100, 101, 103, 104, 105, 106, 9]; // asphalt, gravel, cobblestone, macadam, etc.
    const infra_ids = [18, 132, 133, 47, 48, 49, 51, 52, 53, 54, 55, 56, 57, 23, 24, 25, 36, 37, 38]; 
    const anomaly_ids = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 13, 14, 15, 16, 17, 22, 39, 40, 41, 42, 43, 44, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131];
    
    // Extract numeric ID from "134 - asphalt"
    const match = className.match(/^(\d+)\s-/);
    if (!match) return 'Other';
    const id = parseInt(match[1]);
    
    if (surface_ids.includes(id)) return 'Surfaces';
    if (infra_ids.includes(id)) return 'Infrastructure';
    if (anomaly_ids.includes(id)) return 'Anomalies';
    // Everything else (Cars, people, animals)
    return 'Other';
};'''

content = content.replace(old_getCategory, new_getCategory)

with open('desktop-app/src/renderer.js', 'w', encoding='utf-8') as f:
    f.write(content)
