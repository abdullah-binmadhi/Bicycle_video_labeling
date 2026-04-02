import os
import re

fpath = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html"
with open(fpath, 'r', encoding='utf-8') as f:
    text = f.read()

# I will exactly rip out '<!-- View: Inference -->' all the way to its '</div>\n        </div>\n\n          rder'
# First, extract inference content:
match = re.search(r'(<!-- View: Inference -->.*?</video>\s*<div id="inf-overlay".*?</p>\s*</div>\s*</div>\s*</div>)', text, flags=re.DOTALL)
inf_html = match.group(1) if match else ""

# Remove it and fix the broken string "p-5 bo\n\n          rder" or similar variations that might have scattered carriage returns
if inf_html:
    clean_text = text.replace(inf_html, '')
    # Sometimes it's exactly:
    clean_text = re.sub(r'p-5 bo\s+rder', 'p-5 border', clean_text, flags=re.DOTALL)
    
    # Let's find exactly where view-train closes.
    # It closes right before `<!-- Global Console Output -->`.
    # Wait, let's just insert Inference BEFORE `<!-- Global Console Output -->`. The reason it was broken earlier is probably because `<!-- Global Console Output -->` had flex issues itself, OR because `<!-- View: Inference -->` lacked `w-full max-w-5xl mx-auto`.
    
    # Let's look at `view-train`: `<div id="view-train" class="hidden-view flex flex-col gap-6 w-full max-w-4xl mx-auto pb-10">`
    # Let's look at `view-inference`: `<div id="view-inference" class="hidden-view p-8 space-y-6 h-full overflow-y-auto">` -> wait, `h-full overflow-y-auto`? 
    # If it is placed inside the scrolling container, it shouldn't be h-full overflow-y-auto! Because the WRAPPER is already scrolling!
    # Ah! That's why it was weird. Let's fix the classes of view-inference.
    
    inf_html = inf_html.replace('h-full overflow-y-auto', 'flex flex-col gap-6 w-full max-w-5xl mx-auto pb-10')
    
    # To place it safely, put it just before `<!-- Global Console Output -->`. 
    # But wait, `<!-- Global Console Output -->` is OUTSIDE the scrolling wrapper. 
    # Let's place it BEFORE the nearest closing </div>s prior to Global Console Output.
    
    split_parts = clean_text.split('<!-- Global Console Output -->')
    
    # Usually it's just `</div>\n          </div>\n        </main>` above `<!-- Global Console Output -->`?
    # Let's just append it to the end of the scroll wrapper area.
    # We can inject it after "chart-title">Loss Trajectory</p>\n                <canvas id="lossChart" class="w-full h-full"></canvas>\n              </div>\n            </div>\n          </div>"
    
    anchor = '</canvas>\n              </div>\n            </div>\n          </div>\n\n          </div>\n\n          </div>\n\n          </div>\n\n          </div>'
    if anchor in clean_text:
        inserted = clean_text.replace(anchor, anchor + '\n\n          ' + inf_html + '\n')
    else:
        # fallback: insert before `<!-- Global Console Output -->` but we must put it INSIDE the scroll view.
        # So we inject before the sequence of </div>s that ends the scroll view.
        find_bottom = clean_text.rfind('</div>\n          </div>\n        </div>\n\n        <!-- Global Console Output -->')
        if find_bottom != -1:
            inserted = clean_text[:find_bottom] + '\n\n' + inf_html + '\n' + clean_text[find_bottom:]
        else:
            inserted = clean_text.replace('<!-- Global Console Output -->', inf_html + '\n<!-- Global Console Output -->')
            
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(inserted)
    print("Fixed layout correctly. Cleaned out broken UI and set it in grid.")
else:
    print("Could not find the inference block. Did it get lost?")
