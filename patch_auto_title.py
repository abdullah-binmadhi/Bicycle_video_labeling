html_path = 'desktop-app/src/index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

old_block = """<!-- View: Data & Annotation -->
        <div id="view-data" class="hidden-view flex flex-col gap-6 w-full max-w-4xl mx-auto pb-10">
          <div>
            <h2 class="text-3xl font-medium text-white tracking-tight">Two-Stage Auto Annotation (YOLO-World + CLIP)</h2>
            <p class="text-[#888888] mt-1">Leverage a fully automated 2-stage pipeline. YOLO isolates objects, CLIP tags semantic features.</p>
          </div>"""

new_block = """<!-- View: Data & Annotation -->
        <div id="view-data" class="hidden-view flex flex-col gap-6 w-full max-w-4xl mx-auto pb-10">
          <div>
            <h2 class="text-3xl font-medium text-white tracking-tight">Automated Annotation</h2>
            <p class="text-[#888888] mt-2 text-sm leading-relaxed max-w-3xl">
               Automate your dataset labeling using a state-of-the-art hybrid vision pipeline. 
               <br><br>
               <strong class="text-indigo-400">1. YOLO-World:</strong> Scans the video frames for bounding boxes based on the target vocabulary. It operates zero-shot, meaning it can detect items based purely on text prompts without fine-tuning.
               <br><br>
               <strong class="text-emerald-400">2. CLIP (Contrastive Language-Image Pretraining):</strong> Acts as a semantic refinement layer. The cropped objects from YOLO are passed into CLIP, which reads the visual texture and matches it to detailed descriptive text (e.g., distinguishing a "dry pothole" from a "puddle").
            </p>
          </div>"""

if old_block in html:
    html = html.replace(old_block, new_block)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("Updated HTML title and description")
else:
    print("HTML block not found. Maybe Already updated.")
