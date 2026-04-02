import re
import os

target = "desktop-app/src/index.html"
with open(target, 'r') as f:
    html = f.read()

# 1. Remove all glowing decorative absolute divs
html = re.sub(r'<div class="absolute[^>]*bg-gradient-to-[^>]*blur-[^>]*></div>', '', html)
html = re.sub(r'<div class="absolute[^>]*bg-[A-Za-z0-9]+-500/[0-9]+[^>]*blur-[^>]*></div>', '', html)

# 2. General Glass-Card conversions -> sharp, brutalist, zen
# Change outer wrappers
html = re.sub(r'glass-card rounded-[23]xl border border-white/10', 'border border-[#222] bg-[#0c0c0c] p-8', html)
html = re.sub(r'glass-card rounded-[23]xl p-[468] border border-white/10', 'border border-[#222] bg-[#0c0c0c] p-8', html)
html = re.sub(r'glass-card', 'border border-[#222] bg-[#0c0c0c] p-8', html)

# 3. Strip rounding
html = re.sub(r'\brounded-(xl|2xl|3xl|lg|md)\b', 'rounded-none', html)
html = re.sub(r'\brounded-full\b', 'rounded-none', html)

# 4. Strip shadows & animations
html = re.sub(r'\bshadow-(lg|xl|2xl|inner|sm)\b', '', html)
html = re.sub(r'\bshadow-\[[^\]]+\]\b', '', html)
html = re.sub(r'\banimate-(pulse|bounce|fade-in|ping)\b', '', html)

# 5. Zen Typography & Colors
# Headers
html = re.sub(r'\btext-emerald-[45]00\b', 'text-[#e0e0e0]', html)
html = re.sub(r'\btext-emerald-300\b', 'text-[#c0c0c0]', html)
html = re.sub(r'\btext-blue-[45]00\b', 'text-[#e0e0e0]', html)
html = re.sub(r'\btext-slate-[34]00\b', 'text-[#888888]', html)
html = re.sub(r'\bfont-extrabold\b', 'font-normal tracking-tight', html)
html = re.sub(r'\bfont-bold\b', 'font-medium', html)

# Inputs
html = re.sub(r'\bbg-slate-900/50\b', 'bg-black', html)
html = re.sub(r'\bbg-slate-900/80\b', 'bg-black', html)
html = re.sub(r'\bbg-emerald-900/40\b', 'bg-[#111]', html)
html = re.sub(r'\bborder-white/10\b', 'border-[#333]', html)
html = re.sub(r'\bborder-white/5\b', 'border-[#222]', html)

# Buttons
html = re.sub(r'\bbtn-md join-item bg-slate-700 border-white/10 text-white hover:bg-slate-600\b', 'btn-md join-item bg-transparent border border-[#444] text-[#ccc] hover:bg-[#222] hover:border-[#666] hover:text-white transition-colors rounded-none', html)
html = re.sub(r'\bbtn border-0 bg-blue-600 hover:bg-blue-500 text-white\b', 'btn border border-transparent bg-[#e0e0e0] hover:bg-white text-black rounded-none', html)
html = re.sub(r'\bbtn border-0 bg-emerald-600 hover:bg-emerald-500 text-white\b', 'btn border border-transparent bg-[#e0e0e0] hover:bg-white text-black rounded-none', html)
html = re.sub(r'\bbg-white/10 hover:bg-white/20\b', 'bg-transparent border border-[#333] hover:border-[#888]', html)

# Background layouts
html = re.sub(r'\bfrom-slate-900 via-slate-900 to-black\b', 'bg-black', html)
html = re.sub(r'\bbg-slate-[89]00\b', 'bg-[#0a0a0a]', html)
html = re.sub(r'\bbg-base-300\b', 'bg-[#050505]', html)

# 6. Menu/Sidebar links
html = re.sub(r'\bhover:bg-white/10\b', 'hover:bg-[#1a1a1a] hover:text-white transition-colors rounded-none', html)
html = re.sub(r'\bmenu\b', 'menu text-[#888]', html)

# 7. Remove Emojis
html = html.replace('🎯', '')
html = html.replace('✨', '')
html = html.replace('⚙️', '')
html = html.replace('⚠️', '')
html = html.replace('🟢', '')

# Replace generic "CycleSafe Studio" with an ultra-minimal text badge
# Find the app title and un-round it, remove gradients
html = re.sub(r'<div class="flex items-center gap-3 mb-8">.*?</div>', 
    '''<div class="flex items-center gap-3 mb-10 pb-4 border-b border-[#222]">
        <div class="w-8 h-8 flex items-center justify-center border border-[#e0e0e0] text-[#e0e0e0] text-lg font-mono">CS</div>
        <h1 class="text-xl font-light tracking-wide text-white">CYCLESAFE</h1>
    </div>''', html, flags=re.DOTALL|re.MULTILINE)

# Overrides for DaisyUI step colors explicitly in the style tag or removing class
html = html.replace('step-primary', 'step-neutral')
html = html.replace('step-info', 'step-neutral')
html = html.replace('step-accent', 'step-neutral')
html = html.replace('step-warning', 'step-neutral')
html = html.replace('step-success', 'step-neutral')

with open(target, 'w') as f:
    f.write(html)
print("Zen Theme Applied!")
