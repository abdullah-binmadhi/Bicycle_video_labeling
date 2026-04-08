with open('desktop-app/src/renderer.js', 'r') as f:
    lines = f.readlines()

start = -1
end = -1
for i, l in enumerate(lines):
    if 'window.updateMapState = function()' in l:
        start = i
    if start != -1 and i > start and 'window.updateCharts' in l: # or next function
        pass

for i in range(start, len(lines)):
    if 'window.exportGeospatialCSV' in lines[i]:
        end = i - 1
        break

print(f"Starts at {start}, ends just before {end}")
