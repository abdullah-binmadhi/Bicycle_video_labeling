import re

with open('desktop-app/src/renderer.js', 'r', encoding='utf-8') as f:
    content = f.read()

old_loop = r'''            // Draw either Line segment or Dot
            if \(drawLinesMode && cat === 'Surfaces'\) \{
                // If it's a surface and mode is lines, draw line connecting to last visible surface
                if \(prevSurfacePt\) \{
                    L.polyline\(\[\[prevSurfacePt.lat, prevSurfacePt.lon\], \[pt.lat, pt.lon\]\], \{
                        color: color, // color by current point's surface
                        weight: 4,
                        opacity: 0.6
                    \}\).bindTooltip\(`<b>\$\{s\}</b><br/>Dist: \$\{dist\}m`, \{
                        className: 'bg-\[#111\] text-white border-\[#333\]'
                    \}\).addTo\(geoLayerGroup\);
                \}
            \}
            
            // ALWAYS draw the dot, regardless of mode \(so points don't vanish\)
            L.circleMarker\(\[pt.lat, pt.lon\], \{
                radius: 4,
                fillColor: color,
                color: color,
                weight: 1,
                opacity: 1,
                fillOpacity: 0.8
            \}\).bindTooltip\(`<b>\$\{s\}</b><br/><span class="font-mono text-xs">\$\{pt.plusCode \|\| 'N/A'\}</span><br/>Dist: \$\{dist\}m`, \{
                className: 'bg-\[#111\] text-white border-\[#333\]'
            \}\).addTo\(geoLayerGroup\);'''

new_loop = '''            // Draw either Line segment or Dot
            if (drawLinesMode && cat === 'Surfaces') {
                // In line mode, surfaces ONLY render as a continuous line (NO dots for surfaces)
                if (prevSurfacePt) {
                    L.polyline([[prevSurfacePt.lat, prevSurfacePt.lon], [pt.lat, pt.lon]], {
                        color: color, // color by current point's surface
                        weight: 4,
                        opacity: 0.6
                    }).bindTooltip(`<b>${s}</b><br/>Dist: ${dist}m`, {
                        className: 'bg-[#111] text-white border-[#333]'
                    }).addTo(geoLayerGroup);
                }
            } else {
                // If NOT a surface, or we are in Dots mode, render as a dot
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
            }'''

# Attempt the replace
content = re.sub(old_loop, new_loop, content, flags=re.MULTILINE)

with open('desktop-app/src/renderer.js', 'w', encoding='utf-8') as f:
    f.write(content)
