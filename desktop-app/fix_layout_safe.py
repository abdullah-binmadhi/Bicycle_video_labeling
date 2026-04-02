import os

html_file = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/src/index.html"
with open(html_file, 'r', encoding='utf-8') as f:
    html = f.read()

start_tag = '<!-- View: Inference -->'
end_tag = '<!-- Global Console Output -->'

if start_tag in html and end_tag in html:
    top_split = html.split(start_tag)
    before_inference = top_split[0]
    rest = top_split[1]
    
    inference_split = rest.split(end_tag)
    inference_block = start_tag + inference_split[0]
    
    # 1. Clean out the inference block from where it is right now
    clean_html = before_inference + end_tag + inference_split[1]
    
    # 2. Re-inject the inference block inside the scrolling view area!
    # The scrolling view area ends slightly before `<!-- Global Console Output -->`.
    # Let's target the exact string that marks the end of `view-train`.
    train_anchor = '<!-- Beautiful Canvas Render -->'
    if train_anchor in clean_html:
        split_train = clean_html.split(train_anchor)
        after_train = split_train[1]
        
        end_idx = after_train.find('</canvas>\n              </div>\n            </div>\n          </div>')
        offset = len('</canvas>\n              </div>\n            </div>\n          </div>')
        insert_pos = end_idx + offset
        
        # Inject back inference block properly
        final_html = split_train[0] + train_anchor + after_train[:insert_pos] + '\n\n          ' + inference_block + after_train[insert_pos:]
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(final_html)
        print("Success! Inference View relocated.")
    else:
        print("Anchor missing")
else:
    print("Tags missing")
