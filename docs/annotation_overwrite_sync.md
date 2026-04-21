# Approach 1: Overwrite by Image ID (Annotation State Sync)

## The Core Problem
In the original implementation, the desktop app performed an **"Append-Only"** save operation. 
When reviewing an auto-annotated image, if a user deleted a bounding box in the UI and clicked "Save", the frontend simply sent the *remaining* boxes to the backend. The backend then appended these remaining boxes to the bottom of `master_annotations.csv`.

**The Result:** 
1. The original (incorrect) auto-annotations remained in the CSV.
2. The newly saved annotations were added as duplicates.
3. The "deleted" box was never actually removed from the file, leading to overlapping, incorrect, and duplicate training data.

## The Solution: State Synchronization
To fix this, we change the save operation from "Append-Only" to a full **State Synchronization** for the specific image being edited.

Instead of sending boxes one by one, the frontend will bundle the exact state of the canvas (all visible boxes) and send them as a single update payload tagged with the `image_id`.

## Step-by-Step Workflow

### 1. Frontend: Payload Generation (`src/renderer.js`)
When the user clicks the "[SAVE] Overwrite Frame" button, the frontend logic will:
*   Iterate through the `currentBoxes` array (which represents exactly what the user sees on the canvas, minus any deleted boxes).
*   Convert the display coordinates (Canvas X/Y) back into relative image pixel coordinates (Xmin/Ymin/Xmax/Ymax).
*   Construct a single payload array containing all boxes for the current `image_id`.
*   Send this unified payload to the backend via a new IPC channel: `sync-image-annotations`.

### 2. Backend: Surgical Replacement (`main.js`)
When the backend receives the `sync-image-annotations` IPC event, it performs a 3-step operation to safely update the CSV:

#### Step A: Read & Filter
*   The backend reads the entire `master_annotations.csv` into memory.
*   It iterates through every row.
*   If a row belongs to the specific `image_id` currently being saved, it is **discarded** (effectively deleting all previous annotations for this frame, including the initial auto-annotations).
*   If a row belongs to a *different* image, it is **kept**.

#### Step B: Append New State
*   The backend takes the new payload of boxes received from the frontend.
*   It formats these new boxes into standard CSV rows.
*   It appends these new rows to the filtered memory list created in Step A.

#### Step C: Atomic Write (Safety First)
To prevent data corruption in the event of a crash during the file write process:
*   The backend writes the updated, perfectly synchronized list to a temporary file (e.g., `master_annotations.csv.tmp`).
*   Only after the temporary file is completely and successfully written, the backend instantly swaps it with the original `master_annotations.csv` file.

## Why this Approach is Superior
*   **True Deletions:** Any box deleted in the UI is permanently removed from the CSV, as its original entry is discarded in Step A and never re-written.
*   **Zero Duplicates:** Clicking "Save" multiple times on the same image will simply overwrite that specific image's data with the exact same canvas state, never accumulating duplicate rows.
*   **Robust Data Integrity:** The atomic write process ensures the dataset is never corrupted by a partial file write.
*   **Seamless User Experience:** The user workflow remains exactly the same—review, adjust, hit save, and move on. The complexity is handled entirely behind the scenes.
