# 🚲 CycleSafe Studio & Bicycle Video ML Model: Project Understanding

## 1. Core Architecture & Philosophy
This project solves a complex multimodal ML problem: predicting road surface conditions (asphalt, cobblestone, dirt) and cyclist behavior (pedaling, coasting, braking) efficiently. 

Crucially, it avoids a "circular dependency" trap found in earlier architecture (where vision and IMU were fused directly during active training) by dividing the pipeline into two distinct domains:
- **Offline Vision (Ground Truth Generation):** A HuggingFace CLIP-based zero-shot annotator evaluates video frames and automatically generates probability-based classifications of the road surface.
- **Online/Real-time Physics:** A Transformer-based PyTorch neural network (`Physics1D`) that trains on the generated ground truth labels but takes purely 1D physical telemetry (IMU accelerometer and gyroscope sliding windows) as incoming data.

## 2. Key Modules
### A. The Data Pipeline (`data_pipeline/`)
The backbone that handles heterogeneous sensor fusion.
- **Annotators (`clip_auto_labeler.py`, `clip_interactive.py`):** Automatically tags continuous materials (95% accuracy) and allows single-frame queries for edge cases.
- **Synchronizer (`synchronizer.py`):** Merges low-frequency video ground truth labels (e.g., 10Hz) with high-frequency IMU sensors (e.g., 50Hz) using Pandas `merge_asof` temporal logic based on UNIX NTP timestamps.
- **DSP Filter (`dsp_filter.py`):** Subtracts the known "bicycle bounce rate" (quarter-car model) from raw vibrations using Fourier Transforms, isolating the raw "road signature."

### B. Machine Learning Models
- **Dual-Stream Kinematic Fusion Network (`train_unified.py`):** To prevent high vibrations from corrupting velocity profiles ("Vibration-Velocity Illusion"), the network splits into a two-tower topology.
  - **Stream 1 (High-Frequency Shudder):** 50Hz Acc/Gyr for sudden impacts and suspension displacement.
  - **Stream 2 (Low-Frequency Context):** 1-10Hz GNSS for momentum and steering angles.
- **MultimodalRoadDataset:** Groups data into 50-frame temporal sliding windows for highly contextual transformer analysis.

### C. The Desktop App (`desktop-app/`)
Built with **Electron** and **Node.js**, `CycleSafe Studio` ensures complete local execution.
- By ignoring third-party cloud tools like Roboflow, it guarantees 100% data privacy.
- **App-Based Hybrid System:** A visual UI orchestrating the `clip_auto_labeler`, but seamlessly exposing an HTML5 Canvas to manually draw bounding boxes or type edge-case prompts into the Interactive CLIP Query for the final 5% of problematic frames.

### D. The Agentic Toolkit (`.agent/`)
This project utilizes the intricate **Antigravity Kit** toolkit framework:
- A local AI-orchestration architecture loaded with **20 Specialist Agents**, **36 Modular Skills**, and **11 Action Workflows**.
- Features strict CI/CD and script validation hooks (`verify_all.py`, `checklist.py`) mapped to rigorous clean-code and Socratic problem-solving principles.

## 3. Readiness to Continue
I have fully assimilated the decoupling of the deprecated `LateFusionNetwork` into distinct Vision preprocessing and Physics runtime modules. I comprehend your dual-stream data chunking logic and your Node/Electron-based offline UI pipeline. 

I am confident and ready to assist you in extending the codebase—whether refactoring Electron React components, optimizing PyTorch tensor loaders, executing slash commands, or orchestrating your customized Agent personas!
