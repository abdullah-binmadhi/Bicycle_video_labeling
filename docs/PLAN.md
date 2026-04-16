# Plan: Implement Dynamic Dynamic CSV Parsing in Real-time Inference Renderer (Option A)

## Objective
Update the `desktop-app/src/renderer.js` to dynamically parse the auto-annotation CSV file based on its headers, ensuring compatibility with the Auto-Annotator outputs from the backend pipeline.

## Problem Statement
The Real-Time Inference overlay in `renderer.js` hardcodes column indices (e.g., `p[2]` for confidence) when reading annotation CSVs. The backend pipeline generates fields in the order: `image_id, label_code, class_name, xmin, ymin, xmax, ymax, score`. Because the indices misalign (confidence is at index 7 instead of 2, and `class_name` is at index 2), the bounding box parser evaluates confidence scores as `NaN`, causing the annotations overlay to fail. 

## Scope
- Modify `loadAnnotations` and the bounding-box generation sequence inside `renderer.js` line ~1176.
- Detect CSV headers on the first line.
- Assign mapping logic to index variables `idxImage, idxLabelCode, idxClassName, idxXmin, idxYmin, idxXmax, idxYmax, idxScore`.
- Parse every subsequent row according to these mapped offsets rather than hardcoded 0 to 7 indices.
- Test and verify UI overlay mapping.

## Agents Involved (Orchestration context)
- **project-planner**: Formulate this plan (Current Stage).
- **frontend-specialist**: Will execute the dynamic CSV parser logic inside `renderer.js`.
- **test-engineer**: Will verify logic utilizing dummy dummy output CSV and lint tests.

## Milestone Tasks
- [ ] Determine header order by parsing line `0` of the CSV string data.
- [ ] Fallback to old hardcoded offsets if headers are missing to maintain back-compat.
- [ ] Adapt extraction logic: `const label = p[idxClassName]; const conf = parseFloat(p[idxScore]);`
- [ ] Run scripts tests via `.agent/skills/lint-and-validate/scripts/lint_runner.py` and `security_scan.py` to satisfy orchestration flow.
- [ ] Provide synthesized Orchestration Report.

## Verification
- Load existing Auto-Annotator formatted CSV file into the modified Electron dashboard and watch the Bounding Boxes render successfully overlaying the video feed.
