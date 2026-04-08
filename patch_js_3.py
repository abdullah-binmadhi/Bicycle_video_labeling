import re

with open('desktop-app/src/renderer.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update the 'surfaces' and 'color_map' within initAnalytics map mock data
old_surfaces = r'''        // Generate synthetic initial map data
        const base_lat = 52.5200;
        const base_lon = 13.4050;
        const surfaces = \['Asphalt', 'Gravel', 'Cobble', 'Pothole', 'Speed Bump', 'Bicycle Lane', 'Rail Tracks'\];
        const color_map = \{
            'Asphalt': '#10b981',
            'Gravel': '#f59e0b',
            'Cobble': '#3b82f6',
            'Pothole': '#ef4444', 'Speed Bump': '#a855f7', 'Bicycle Lane': '#2dd4bf', 'Rail Tracks': '#64748b'
        \};'''

new_surfaces = '''        // Generate synthetic initial map data
        const base_lat = 52.5200;
        const base_lon = 13.4050;
        const surfaces = ['134 - asphalt', '8 - gravel', '19 - cobblestone', '1 - potholes', '5 - speed_bump', '133 - bicycle_lane', '18 - rail_tracks'];
        const color_map = {
            '134 - asphalt': '#10b981',
            '8 - gravel': '#f59e0b',
            '19 - cobblestone': '#3b82f6',
            '1 - potholes': '#ef4444', '5 - speed_bump': '#a855f7', '133 - bicycle_lane': '#2dd4bf', '18 - rail_tracks': '#64748b'
        };'''

content = re.sub(old_surfaces, new_surfaces, content, flags=re.MULTILINE)


# 2. Add 'getCategory' global helper function before updateMapState
helper_injection = '''window.getCategory = function(className) {
    const sLow = className.toLowerCase();
    if (sLow.includes('asphalt') || sLow.includes('gravel') || sLow.includes('cobble') || sLow.includes('134') || sLow.includes('8') || sLow.includes('19')) return 'Surfaces';
    if (sLow.includes('bicycle') || sLow.includes('rail') || sLow.includes('track') || sLow.includes('133') || sLow.includes('18')) return 'Infrastructure';
    if (sLow.includes('pothole') || sLow.includes('bump') || sLow.includes('1') || sLow.includes('5') || sLow.includes('crack')) return 'Anomalies';
    return 'Other';
};'''

old_class_state = '''window.classState = {};

window.updateMapState = function() {'''

new_class_state = f'''{helper_injection}

window.classState = {{}};

window.updateMapState = function() {{'''

content = content.replace(old_class_state, new_class_state)


# 3. Rewrite updateMapState's drawing loop
old_draw_loop = r'''    let prevPt = null;
    let prevColor = null;
    let prevVisible = false;

    // We process sequentially, connecting visible points
    for \(const pt of window.currentGeoData\) \{
        if \(!pt.surface\) continue;
        let s = pt.surface;
        let isVisible = window.classState\[s\] && window.classState\[s\].visible;
        let color = window.classState\[s\] \? window.classState\[s\].color : '#fff';
        let dist = parseFloat\(pt.distance_m \|\| 0\);

        if \(isVisible\) \{
            // Aggregate distance
            if \(!distanceAgg\[s\]\) distanceAgg\[s\] = 0;
            distanceAgg\[s\] \+= dist;

            // Draw either Line segment or Dot
            if \(drawLinesMode\) \{
                if \(prevVisible && prevPt\) \{
                    L.polyline\(\[\[prevPt.lat, prevPt.lon\], \[pt.lat, pt.lon\]\], \{
                        color: color, // color by current point's surface
                        weight: 4,
                        opacity: 0.8
                    \}\).bindTooltip\(`<b>\$\{s\}</b><br/>Dist: \$\{dist\}m`, \{
                        className: 'bg-\[#111\] text-white border-\[#333\]'
                    \}\).addTo\(geoLayerGroup\);
                \}
            \} else \{
                L.circleMarker\(\[pt.lat, pt.lon\], \{
                    radius: 4,
                    fillColor: color,
                    color: color,
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.8
                \}\).bindTooltip\(`<b>\$\{s\}</b><br/><span class="font-mono text-xs">\$\{pt.plusCode \|\| 'N/A'\}</span><br/>Dist: \$\{dist\}m`, \{
                    className: 'bg-\[#111\] text-white border-\[#333\]'
                \}\).addTo\(geoLayerGroup\);
            \}
        \}

        prevPt = pt;
        prevVisible = isVisible;
        prevColor = color;
    \}'''

new_draw_loop = '''    let prevSurfacePt = null;

    // We process sequentially, connecting visible points
    for (const pt of window.currentGeoData) {
        if (!pt.surface) continue;
        let s = pt.surface;
        let isVisible = window.classState[s] && window.classState[s].visible;
        let color = window.classState[s] ? window.classState[s].color : '#fff';
        let dist = parseFloat(pt.distance_m || 0);
        let cat = window.getCategory(s);

        if (isVisible) {
            // Aggregate distance
            if (!distanceAgg[s]) distanceAgg[s] = 0;
            distanceAgg[s] += dist;

            // Draw either Line segment or Dot
            if (drawLinesMode && cat === 'Surfaces') {
                // If it's a surface and mode is lines, draw line connecting to last visible surface
                if (prevSurfacePt) {
                    L.polyline([[prevSurfacePt.lat, prevSurfacePt.lon], [pt.lat, pt.lon]], {
                        color: color, // color by current point's surface
                        weight: 4,
                        opacity: 0.8
                    }).bindTooltip(`<b>${s}</b><br/>Dist: ${dist}m`, {
                        className: 'bg-[#111] text-white border-[#333]'
                    }).addTo(geoLayerGroup);
                }
            } else {
                // Dot mode OR if it's an Anomaly/Infrastructure (they should always drop a dot!)
                L.circleMarker([pt.lat, pt.lon], {
                    radius: 4,
                    fillColor: color,
                    color: color,
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.8
                }).bindTooltip(`<b>${s}</b><br/><span class="font-mono text-xs">${pt.plusCode || 'N/A'}</span><br/>Dist: ${dist}m`, {
                    className: 'bg-[#111] text-white border-[#333]'
                }).addTo(geoLayerGroup);
            }
        }

        if (cat === 'Surfaces') {
            if (isVisible) {
                prevSurfacePt = pt;
            } else {
                // Break path if there's a hidden surface segment
                prevSurfacePt = null;
            }
        }
    }'''

content = re.sub(old_draw_loop, new_draw_loop, content, flags=re.MULTILINE)

# 4. Replace custom categorize logic in renderLegend to use getCategory
old_render_categorize = r'''    // Segregate based on custom categories
    const categories = \{
        'Surfaces': \[\],
        'Infrastructure': \[\],
        'Anomalies': \[\],
        'Other': \[\]
    \};
    
    for \(const className in window.classState\) \{
        const sLow = className.toLowerCase\(\);
        if \(sLow.includes\('asphalt'\) \|\| sLow.includes\('gravel'\) \|\| sLow.includes\('cobble'\) \|\| sLow.includes\('134'\) \|\| sLow.includes\('8'\) \|\| sLow.includes\('19'\)\) \{
            categories\['Surfaces'\].push\(className\);
        \} else if \(sLow.includes\('bicycle'\) \|\| sLow.includes\('rail'\) \|\| sLow.includes\('track'\) \|\| sLow.includes\('133'\) \|\| sLow.includes\('18'\)\) \{
            categories\['Infrastructure'\].push\(className\);
        \} else if \(sLow.includes\('pothole'\) \|\| sLow.includes\('bump'\) \|\| sLow.includes\('1'\) \|\| sLow.includes\('5'\) \|\| sLow.includes\('crack'\)\) \{
            categories\['Anomalies'\].push\(className\);
        \} else \{
            categories\['Other'\].push\(className\);
        \}
    \}'''

new_render_categorize = '''    // Segregate based on custom categories
    const categories = {
        'Surfaces': [],
        'Infrastructure': [],
        'Anomalies': [],
        'Other': []
    };
    
    for (const className in window.classState) {
        categories[window.getCategory(className)].push(className);
    }'''

content = re.sub(old_render_categorize, new_render_categorize, content, flags=re.MULTILINE)

# 5. Fix defaultClasses inside renderLegend
old_default_classes = r"const defaultClasses = \['Asphalt', 'Gravel', 'Cobble', 'Pothole', 'Speed Bump', 'Bicycle Lane', 'Rail Tracks'\];"
new_default_classes = r"const defaultClasses = ['134 - asphalt', '8 - gravel', '19 - cobblestone', '1 - potholes', '5 - speed_bump', '133 - bicycle_lane', '18 - rail_tracks'];"
content = re.sub(old_default_classes, new_default_classes, content)

with open('desktop-app/src/renderer.js', 'w', encoding='utf-8') as f:
    f.write(content)

