import re

path = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html"
with open(path, "r") as f:
    html = f.read()

# 1. Remove gradient from title
html = html.replace(
    '<a class="text-xl font-extrabold tracking-tight bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">CycleSafe Studio</a>',
    '<a class="text-xl font-extrabold tracking-tight text-white drop-shadow-sm">CycleSafe Studio</a>'
)

# 2. Re-architect the main wrapping to make console truly fixed at bottom
# Change main from scrolling to fixed flex column
html = html.replace(
    '<main class="flex-1 p-8 overflow-y-auto flex flex-col gap-8 relative z-0">',
    '<main class="flex-1 flex flex-col overflow-hidden relative z-0">\n        <!-- Scrolling Views Wrapper -->\n        <div class="flex-1 p-8 overflow-y-auto flex flex-col gap-8">'
)

# 3. Close the scrolling wrapper right before the console
console_start = '        <!-- Global Console Output -->'
html = html.replace(
    console_start,
    '        </div>\n\n' + console_start
)

# 4. Update the console wrapper to remove sticky bottom-0 (its now just a flex item at the bottom of main)
# and give it a structural background
html = html.replace(
    '<div class="w-full max-w-5xl mx-auto z-20 sticky bottom-0">',
    '<div class="w-full flex-shrink-0 z-20 border-t border-white/10 bg-slate-950/80 backdrop-blur-3xl shadow-[0_-20px_40px_-15px_rgba(0,0,0,0.7)]">\n          <div class="w-full max-w-5xl mx-auto">'
)

# We need to add one more closing div since we wrapped the max-w-xl mx-auto inside the new full-width container
# Let's use regex rather than simple replacement to ensure we don't accidentally match bad sections.
html = re.sub(
    r'</div>\s*</div>\s*</main>',
    '</div>\n          </div>\n        </div>\n\n      </main>',
    html
)

with open(path, "w") as f:
    f.write(html)

print("UI successfully updated!")
