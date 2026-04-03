with open("desktop-app/src/index.html", "r") as f:
    text = f.read()

text = text.replace('Vision Embeddings</h3>', 'Input Parameters</h3>')
text = text.replace('IMU Physics Timeline</h3>', 'Temporal Logic</h3>')
text = text.replace('2. Auto Annotation (CLIP)', '2. Auto Annotation')

# Hide the Inference Pipeline on real-time inference page
target = '''                      <div>
                          <h3 class="text-[#e0e0e0] font-medium tracking-widest text-sm uppercase flex items-center gap-2">
                              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                              Inference Pipeline
                          </h3>
                          <p class="text-xs text-[#888888]">Processing LM-17.06_multi_sensor_aligned.csv Output</p>
                      </div>'''

replacement = '''                      <div class="hidden">
                          <h3 class="text-[#e0e0e0] font-medium tracking-widest text-sm uppercase flex items-center gap-2">
                              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                              Inference Pipeline
                          </h3>
                          <p class="text-xs text-[#888888]">Processing LM-17.06_multi_sensor_aligned.csv Output</p>
                      </div>'''

text = text.replace(target, replacement)

# TEST PHASE replace if existing
text = text.replace('TEST PHASE: Dual-Stream Physics Engine', 'Inference Pipeline')

with open("desktop-app/src/index.html", "w") as f:
    f.write(text)
