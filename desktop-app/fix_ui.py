import re

path = 'src/index.html'
with open(path, 'r') as f:
    content = f.read()

# 1. Update Headings
content = content.replace('2. Ensemble Pipeline Annotation (YOLO + DINO + CLIP)', '2. OWLv2 Zero-Shot Annotation')
content = content.replace('100% automated offline pipeline. YOLO generates bounding boxes from a custom vocabulary, Grounding DINO ensures spatial accuracy, and CLIP tags deep semantics.', '100% automated offline pipeline. OWLv2 generates highly accurate bounding boxes from a natural language custom vocabulary without relying on pre-trained YOLO/DINO models.')

content = content.replace('Run automated workflows with Grounding DINO zero-shot, YOLOv11 inference, and CLIP profiling.', 'Run automated workflows with OWLv2 zero-shot inference and text-based vocabulary.')
content = content.replace('3. YOLO Target Vocabulary', '3. OWLv2 Target Vocabulary')
content = content.replace('Ensemble Pipeline (YOLO + DINO + CLIP)', 'OWLv2 Pipeline (Zero-Shot BBox)')

# Fix paragraph
content = content.replace('Standard road classification models rely entirely on live camera feeds (like YOLO). These systems fail in poor conditions', 'Standard road classification models rely entirely on limited categorical vocabulary. These systems fail in poor conditions')

# Remove duplicate 133 bicycle lane
content = content.replace('<option value="133 - bicycle_lane">133 - bicycle_lane</option>', '')

# Properly remove the 133 checkbox block without deleting all divs
broken_checkbox = """                </div><div class="flex items-center gap-2 mb-1">
                    <input type="checkbox" id="clip-cls-133 - bicycle_lane" value="133 - bicycle_lane" checked="" class="checkbox checkbox-xs checkbox-primary clip-class-checkbox">
                    <label for="clip-cls-133 - bicycle_lane" class="text-[10px] sm:text-xs truncate text-[#e0e0e0] cursor-pointer" title="133 - bicycle_lane">133 - bicycle_lane</label>"""
content = content.replace(broken_checkbox, '')

broken_checkbox_v2 = """<div class="flex items-center gap-2 mb-1">
                    <input type="checkbox" id="clip-cls-133 - bicycle_lane" value="133 - bicycle_lane" checked="" class="checkbox checkbox-xs checkbox-primary clip-class-checkbox">
                    <label for="clip-cls-133 - bicycle_lane" class="text-[10px] sm:text-xs truncate text-[#e0e0e0] cursor-pointer" title="133 - bicycle_lane">133 - bicycle_lane</label>
                </div>"""
content = content.replace(broken_checkbox_v2, '')

with open(path, 'w') as f:
    f.write(content)

print("Fixed UI correctly.")
