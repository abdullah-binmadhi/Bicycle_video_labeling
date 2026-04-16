## 🧠 Brainstorm: Unifying Annotation Formats (Auto vs Manual vs Gallery Review)

### Context
You correctly identified a massive architectural flaw in the current labeling workflow. Currently:
1. **Auto-Annotation Pipeline** writes to strict CSV structure (`image_id, label, xmin, ymin, xmax, ymax`).
2. **Video Manual Labeling** writes to `manual_annotations.csv` using a different structure (`video, timestamp, x, y, w, h`).
3. **Dataset Review Gallery** (The HTML snippet you shared) **doesn't write a CSV at all!** When you click "Overwrite Frame", it burns the bounding box directly onto the JPEG pixels (`ctx.drawImage`) and overwrites the image file. This is highly problematic because the YOLO/PyTorch trainers cannot read burned-in pixels—they need coordinate data.

If we don't unify these, your training pipeline will ignore any manual corrections you make in the gallery, and it will crash when trying to merge the video-manual CSV.

Here are 3 ways to fix this.

---

### Option A: The Unified IPC Data Access Layer (Centralized CSV)
Move all file writing out of the frontend `renderer.js` and into the Electron backend via an IPC call. Whether the data comes from the Auto-Annotator, the Video Manual Labeler, or the Review Gallery, the frontend sends a standardized object: `{ imageRef, boxes: [x1, y1, x2, y2], label, confidence, source }`. The backend's `SchemaValidator` writes it to a single `master_annotations.csv` format universally understood by PyTorch.

✅ **Pros:**
- Complete unity. Only ONE schema exists for the entire app.
- Extensively stops HTML bugs from breaking your dataset.
- Fixes the Gallery bug by forcing the gallery to save coordinate data alongside the image.

❌ **Cons:**
- Requires refactoring `manager.js` (IPC) and replacing the `fs.appendFile` blocks in `renderer.js`.

📊 **Effort:** Medium

---

### Option B: The "Just-In-Time" Python Merge Script (Lazy Unification)
Let the frontend continue being messy. The Video Labeler keeps writing `manual_annotations.csv` (x, y, w, h format) and the Review Gallery gets patched to write a `reviewed_annotations.csv`. Then, we update `train_unified.py` to run a pre-processing function that maps, scales, translates, and combines all three separate CSVs into one unified PyTorch tensor format right before training starts.

✅ **Pros:**
- Minimal changes to the complex frontend JS code.
- Python is much better suited to merging/filtering standard pandas DataFrame structures.

❌ **Cons:**
- High technical debt.
- Doesn't stop the UI from generating conflicting datasets.

📊 **Effort:** Low

---

### Option C: Migrate entirely to standard COCO JSON
Abandon CSV altogether for bounding boxes. Implement a lightweight library that reads/writes directly to the strict COCO JSON format. Since COCO supports `{images: [...], annotations: [...]}` at scale, any time the User draws a box in the Gallery, or stops a video, we just append an annotation node to the JSON.

✅ **Pros:**
- Hugely professional. COCO JSON is natively supported by 99% of computer vision libraries implicitly.
- Very reliable.

❌ **Cons:**
- Complete rewrite of your Dataset format.

📊 **Effort:** High

---

## 💡 Recommendation

**Option A**. You already have a great `SchemaValidator` built in Python. We just need to stop the Javascript UI from writing random custom CSV formats. We should mandate that the "Overwrite Frame" gallery button loops through your `currentBoxes` array, captures the `(x, y, w, h)`, and formats them exactly to your Auto-Annotation schema. 

What direction would you like to explore?
