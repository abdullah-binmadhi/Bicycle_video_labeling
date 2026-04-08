import json
import re

with open('config/labels.json', 'r', encoding='utf-8') as f:
    labels_data = json.load(f)

# Extract vocabulary keys
vocab_keys = list(labels_data.keys())

with open('desktop-app/src/renderer.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update updateMapState to STILL draw circle markers for Surfaces when in line mode.
old_draw_loop = r'''            // Draw either Line segment or Dot
            if \(drawLinesMode && cat === 'Surfaces'\) \{
                // If it's a surface and mode is lines, draw line connecting to last visible surface
                if \(prevSurfacePt\) \{
                    L.polyline\(\[\[prevSurfacePt.lat, prevSurfacePt.lon\], \[pt.lat, pt.lon\]\], \{
                        color: color, // color by current point's surface
                        weight: 4,
                        opacity: 0.8
                    \}\).bindTooltip\(`<b>\$\{s\}</b><br/>Dist: \$\{dist\}m`, \{
                        className: 'bg-\[#111\] text-white border-\[#333\]'
                    \}\).addTo\(geoLayerGroup\);
                \}
            \} else \{
                // Dot mode OR if it's an Anomaly/Infrastructure \(they should always drop a dot!\)
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
            \}'''

new_draw_loop = '''            // Draw either Line segment or Dot
            if (drawLinesMode && cat === 'Surfaces') {
                // If it's a surface and mode is lines, draw line connecting to last visible surface
                if (prevSurfacePt) {
                    L.polyline([[prevSurfacePt.lat, prevSurfacePt.lon], [pt.lat, pt.lon]], {
                        color: color, // color by current point's surface
                        weight: 4,
                        opacity: 0.6
                    }).bindTooltip(`<b>${s}</b><br/>Dist: ${dist}m`, {
                        className: 'bg-[#111] text-white border-[#333]'
                    }).addTo(geoLayerGroup);
                }
            }
            
            // ALWAYS draw the dot, regardless of mode (so points don't vanish)
            L.circleMarker([pt.lat, pt.lon], {
                radius: 4,
                fillColor: color,
                color: color,
                weight: 1,
                opacity: 1,
                fillOpacity: 0.8
            }).bindTooltip(`<b>${s}</b><br/><span class="font-mono text-xs">${pt.plusCode || 'N/A'}</span><br/>Dist: ${dist}m`, {
                className: 'bg-[#111] text-white border-[#333]'
            }).addTo(geoLayerGroup);'''

content = re.sub(old_draw_loop, new_draw_loop, content, flags=re.MULTILINE)

# 2. Update defaultClasses to include ALL vocabulary from config
vocab_js_array = json.dumps(vocab_keys)

old_default = r"const defaultClasses = \['134 - asphalt', '8 - gravel', '19 - cobblestone', '1 - potholes', '5 - speed_bump', '133 - bicycle_lane', '18 - rail_tracks'\];"
new_default = f"const defaultClasses = {vocab_js_array};"
content = re.sub(old_default, new_default, content)

# 3. Update getCategory to be much more robust since we have 135 classes.
# Road surfaces: asphalt, gravel, cobblestone, macadam, concrete, dirt_road, brick_paving, block_cracking, etc.
# Actually, the user says there are redundant options and some aren't numbered. That refers to `window.classState`.
# We need to make sure when we render the legend, the classes only come from defaultClasses!
# Currently `window.classState` might populate from map mock strings or bad data.

old_render = '''    for (const className in window.classState) {
        categories[window.getCategory(className)].push(className);
    }'''

new_render = '''    // Only render exact keys that are in defaultClasses (YOLO Vocab), preventing unnumbered/redundant junk.
    for (const className in window.classState) {
        if (defaultClasses.includes(className)) {
            categories[window.getCategory(className)].push(className);
        }
    }'''
content = content.replace(old_render, new_render)


with open('desktop-app/src/renderer.js', 'w', encoding='utf-8') as f:
    f.write(content)
