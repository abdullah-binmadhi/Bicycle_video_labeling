import re

html_path = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html"

with open(html_path, "r") as f:
    html = f.read()

# Try a robust split format
# Split into 3 parts: Header, Features, Legacy
hero_split = html.split('<!-- Features Grid -->')

if len(hero_split) == 2:
    part1_hero = hero_split[0]
    rest = hero_split[1]
    
    steps_split = rest.split('<!-- Legacy Pipeline Steps -->')
    if len(steps_split) == 2:
        features = steps_split[0]
        legacy_and_rest = steps_split[1]
        
        # We need to extract the closing tags of the view-instructions div
        # legacy ends at </div>\n\n          <!-- View: Extract Frames -->
        end_marker = '</div>\n\n          <!-- View: Extract Frames -->'
        end_split = legacy_and_rest.split(end_marker)
        
        if len(end_split) == 2:
            legacy = end_split[0]
            rest_of_html = end_marker + end_split[1]
            
            # Clean up text
            legacy = legacy.replace("Legacy Training Pipeline Roadmap", "Training Pipeline Roadmap")
            legacy = legacy.replace("bg-slate-900/30", "bg-slate-900/30 mb-8 mt-6")
            
            # Reassemble
            new_html = part1_hero + '<!-- Training Pipeline Steps -->\n' + legacy + '\n<!-- Features Grid -->\n' + features + end_marker + end_split[1]
            
            with open(html_path, "w") as f:
                f.write(new_html)
            print("Successfully re-ordered the sections!")
        else:
            print("Failed to find end marker")
    else:
        print("Failed to split legacy steps")
else:
    print("Failed to split features")