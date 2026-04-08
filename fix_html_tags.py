with open("desktop-app/src/index.html", "r") as f:
    text = f.read()

# Fix accidentally duplicated tag
text = text.replace(
    '        <li class="menu text-[#888] text-[#888]-title text-slate-500 uppercase tracking-widest text-[10px]"><span>Getting Started</span></li>',
    '        <li class="menu-title text-slate-500 uppercase tracking-widest text-[10px]"><span>Getting Started</span></li>'
)
text = text.replace(
    '        <li class="menu text-[#888] text-[#888]-title mt-4 text-slate-500 uppercase tracking-widest text-[10px]"><span>Pipeline Operations</span></li>',
    '        <li class="menu-title mt-4 text-slate-500 uppercase tracking-widest text-[10px]"><span>Pipeline Operations</span></li>'
)
text = text.replace(
    '        <li class="menu text-[#888] text-[#888]-title mt-4 text-slate-500 uppercase tracking-widest text-[10px]"><span>Analysis Results</span></li>',
    '        <li class="menu-title mt-4 text-slate-500 uppercase tracking-widest text-[10px]"><span>Analysis Results</span></li>'
)

# And fix the class list issue causing it to glitch
text = text.replace(
    '<ul class="menu text-[#888] text-[#888] w-64 p-4 gap-2 border-r border-[#222] bg-[#0a0a0a]/40 backdrop-blur-sm z-10 font-medium">',
    '<ul class="menu text-[#888] w-64 p-4 gap-2 border-r border-[#222] bg-[#0a0a0a]/40 backdrop-blur-sm z-10 font-medium">'
)

with open("desktop-app/src/index.html", "w") as f:
    f.write(text)

