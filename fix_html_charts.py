import re

with open('desktop-app/src/index.html', 'r') as f:
    text = f.read()

# I want to delete the Charts Row completely:
# This contains the Confusion Matrix and Per-Class Accuracy
charts_row_regex = re.compile(
    r'<!-- Charts Row Header & Filter -->.*?<!-- Advanced Analytics Row -->',
    re.DOTALL
)

# And inside Advanced Analytics Row, I want to delete the Top Row 2x1 containing:
# Loss Convergence Curve and Temporal Stability (Flicker)
advanced_row_regex = re.compile(
    r'<!-- Top Row 2x1 -->.*?<!-- Bottom Row 2x1 -->',
    re.DOTALL
)

# Also delete "Data Distribution" which is the first half of "Bottom Row 2x1"
# And then update "Total Distance per Surface (m)" to be full width or just keep it as is.
data_dist_regex = re.compile(
    r'<div class="border border-\[#222\] bg-\[#0c0c0c\] p-6 flex flex-col items-center min-h-\[300px\]">\s*<h3 class="text-fuchsia-400 font-medium tracking-widest text-xs uppercase self-start mb-4 w-full border-b border-\[#333\] pb-2">Data Distribution</h3>\s*<div class="w-full h-full relative h-\[250px\]">\s*<canvas id="distribution-canvas" class="w-full h-full"></canvas>\s*</div>\s*</div>',
    re.DOTALL
)

new_text = charts_row_regex.sub('<!-- Advanced Analytics Row -->', text)
new_text = advanced_row_regex.sub('<!-- Bottom Row -->', new_text)
new_text = data_dist_regex.sub('', new_text)

# Fix the grid for the remaining distance chart so it spans correctly instead of being 1 of 2 columns
# Look for: <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full"> right after <!-- Bottom Row -->
bottom_row_grid_regex = re.compile(
    r'<!-- Bottom Row -->\s*<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">'
)
new_text = bottom_row_grid_regex.sub('<!-- Bottom Row -->\n      <div class="grid grid-cols-1 gap-6 w-full">', new_text)

with open('desktop-app/src/index.html', 'w') as f:
    f.write(new_text)

print("Replacement applied")
