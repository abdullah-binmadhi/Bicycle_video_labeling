import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update Sidebar Link
html = html.replace('Auto-Annotation (CLIP)', 'Auto Annotation')

# 2. Update Overview and Docs Name from "Live Training Trajectories" to "Hyperparameters"
html = html.replace('Live Training Trajectories</h3>', 'Hyperparameters</h3>')

# Also replace the description? The user just said "change Live Training Trajectories to Hypeparameters to make it consistent".
# Wait, let's also fix the SVG maybe if they want it consistent. The request: "change Live Training Trajectories to Hypeparameters to make it consistent"
html = html.replace('Live Training Trajectories', 'Hyperparameters')

# 3. Real-Time Inference Page cleanups:
# Remove TEST PHASE: Dual-Stream Physics Engine header
new_header1 = '''<h3 class="text-[#e0e0e0] font-medium tracking-widest text-sm uppercase flex items-center gap-2">
                              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                              Inference Pipeline
                          </h3>'''

html = re.sub(
    r'<h3[^>]*>\s*<svg[^>]*>.*?</svg>\s*TEST PHASE: Dual-Stream Physics Engine\s*</h3>',
    new_header1,
    html,
    flags=re.DOTALL
)

# 4. Remove the Advanced Telemetry Array (Features 3, 4, 5) which contains the 
# GPS Velocity Fusion, Anomaly Gate (OOD), Active Learning Routing
import sys
# A bit dangerous but let's try replacing the exact block start/end
start_idx = html.find('<!-- NEW: Real-Time Advanced Telemetry Array (Features 3, 4, 5) -->')
end_idx = html.find('<!-- View: Analytics (Feature 4, 8) -->')

# Wait, we need to make sure we don't accidentally wipe out the end </div> for the `view-inference` div.
if start_idx != -1 and end_idx != -1:
    # Delete from start_idx up to the closing tags prior to view-analytics.
    # Since we want to just remove the features grid div, maybe we can find the end of that grid.
    pass

# Read file line by line to delete properly
lines = html.split('\\n')
new_lines = []
skip = False
for line in lines:
    if '<!-- NEW: Real-Time Advanced Telemetry Array' in line:
        skip = True
    
    if '<!-- View: Analytics (Feature 4, 8) -->' in line:
        skip = False
        new_lines.append('      </div> <!-- End of view-inference -->')
        
    if skip and '<!-- End of view-inference -->' in line:
        pass # Handle manually above
        
    if not skip:
        new_lines.append(line)

final_html = '\\n'.join(new_lines)
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(final_html)

print("Final HTML updates applied!")
