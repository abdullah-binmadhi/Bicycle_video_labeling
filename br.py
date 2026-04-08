with open('desktop-app/src/renderer.js', 'r') as f:
    text = f.read()

start_idx = text.find('window.updateMapState = function() {')
sub = text[start_idx:start_idx+5816+1]
lines_before = text[:start_idx].count('\n')
lines_sub = sub.count('\n')
print("Starts at line:", lines_before + 1)
print("Ends at line:", lines_before + 1 + lines_sub)
