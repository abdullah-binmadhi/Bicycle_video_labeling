---
source: Official docs
library: Grounding DINO
package: grounding-dino
topic: ml-pipeline-usage
fetched: 2026-04-10T00:00:00Z
official_docs: https://github.com/IDEA-Research/GroundingDINO
---

## Model Pipeline & Usage Examples

### Core Setup & Inference Pipeline

The core inference pipeline for Grounding DINO involves loading the model, processing the image and text prompt, and extracting bounding boxes and labels.

```python
from groundingdino.util.inference import load_model, load_image, predict, annotate
import cv2

# 1. Load Model
model = load_model("groundingdino/config/GroundingDINO_SwinT_OGC.py", "weights/groundingdino_swint_ogc.pth")

IMAGE_PATH = "weights/dog-3.jpeg"
# 2. Format Text Prompt (Crucial: separate categories with periods)
TEXT_PROMPT = "chair . person . dog ." 
BOX_TRESHOLD = 0.35
TEXT_TRESHOLD = 0.25

# 3. Load Image
image_source, image = load_image(IMAGE_PATH)

# 4. Predict
boxes, logits, phrases = predict(
    model=model,
    image=image,
    caption=TEXT_PROMPT,
    box_threshold=BOX_TRESHOLD,
    text_threshold=TEXT_TRESHOLD
)

# 5. Annotate and Save
annotated_frame = annotate(image_source=image_source, boxes=boxes, logits=logits, phrases=phrases)
cv2.imwrite("annotated_image.jpg", annotated_frame)
```

### Prompting Rules & Label Formatting

1. **Category Separation**: Always separate different object categories with a period (`.`).
   * Example: `"chair . person . dog ."`
2. **Text vs Box Thresholds**:
   * `box_threshold`: Filters the initial bounding box predictions based on maximum similarity score.
   * `text_threshold`: Filters which words are extracted as predicted labels for a given box.
3. **Complex Phrase Grounding**: To extract specific phrases from a sentence, use token spans.
   * Example prompt: `"There is a cat and a dog in the image ."`
   * Token spans: `"[[[9, 10], [11, 14]], [[19, 20], [21, 24]]]"` specifies the exact character spans for "a cat" and "a dog".

### Command Line Interface Usage

```bash
python demo/inference_on_a_image.py \
  -c groundingdino/config/GroundingDINO_SwinT_OGC.py \
  -p weights/groundingdino_swint_ogc.pth \
  -i image_you_want_to_detect.jpg \
  -o "dir you want to save the output" \
  -t "chair . person . dog ." \
  [--cpu-only] 
```

Using token spans for precise phrase matching:
```bash
python demo/inference_on_a_image.py \
  -c groundingdino/config/GroundingDINO_SwinT_OGC.py \
  -p ./groundingdino_swint_ogc.pth \
  -i .asset/cat_dog.jpeg \
  -o logs/1111 \
  -t "There is a cat and a dog in the image ." \
  --token_spans "[[[9, 10], [11, 14]], [[19, 20], [21, 24]]]"
```
