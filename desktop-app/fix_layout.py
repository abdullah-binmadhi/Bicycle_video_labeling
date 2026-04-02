import os
import re

html_file = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html"
with open(html_file, 'r', encoding='utf-8') as f:
    html = f.read()

# I messed up by inserting view-inference BEFORE the global console output, but 
# immediately replacing `<!-- Global Console Output -->`.
# Wait, let's just find the exact block and move it. 

# Let's extract the Inference block. Note it has nested divs. We'll use a reliable split.
blocks = html.split('<!-- View: Inference -->')
if len(blocks) > 1:
    top_part = blocks[0]
    bottom_part = blocks[1]
    
    # We need to find the end of view-inference. It ends right before <!-- Global Console Output -->
    bottom_splits = bottom_part.split('<!-- Global Console Output -->')
    inference_div_content = bottom_splits[0]
    rest_of_html = '<!-- Global Console Output -->' + bottom_splits[1]
    
    # Let's clean up the inference_div_content (it might have extra closing divs that belong to the main wrapper!)
    # Actually, in build_viz.py I replaced `<!-- Global Console Output -->` with the new view.
    # So the closing divs that were BEFORE `<!-- Global Console Output -->` were NOT replaced, they are still above `<!-- View: Inference -->`!
    # Let's verify this in the original string.
    
    # Let's look at the raw html lines where it goes from view-train to view-inference:
    # </div> <!-- stats -->
    # </div> <!-- view-train -->
    # </div> <!-- scroll wrapper -->
    # </div> <!-- flex-1 bg-slate -->
    # </div> <!-- flex-1 (main content layout inner) --> ... wait, let's fix it properly.

    pass # let's run a script that prints to stdout so we can see exactly what to do.
