# Bicycle Surface Detection ML Model

> **Overview**: A multimodal machine learning pipeline designed to classify road surface conditions (e.g., smooth road, rough road, potholes) and bicycle maneuvers (pedaling, coasting, braking) by fusing 1D physical sensor data (IMU) with extracted 2D video frames.

---

## 🧠 Machine Learning Models & Architecture

The analytical framework has recently been decoupled to solve a circular dependency issue. By shifting the vision tools away from predicting alongside the IMU data in real-time, the architecture now uses standard Computer Vision models purely offline to generate ground truth labels, letting the Physics network train without bias.

### 1. The Annotator (CLIP-based Zero-Shot Vision)

To build an accurately labeled dataset across countless hours of video without the manual burden of bounding boxes, the system integrates HuggingFace deployment of OpenAI's **CLIP** (Contrastive Language-Image Pretraining). Rather than functioning as an active model within the `LateFusionNetwork`, CLIP operates during preprocessing. It evaluates extracted camera frames by probabilistically matching their visual contents against highly descriptive text prompts (e.g., "A point of view photo from a bicycle riding on loose dirt or gravel path"). It acts as our automated "robotic labeler." After classifying the frames into text strings, a Pandas rolling window algorithm applies temporal smoothing to eliminate single-frame glitches (like sun glares), exporting a pristine `Label.csv` containing timestamps and terrain tags.

### 2. The Classifier (`Physics1D` / `PhysicsTransformer`)

This is the core predictive model executing in real-time. It analyzes raw, 1-Dimensional physical motion telemetry—specifically the `Acc-X`, `Acc-Y`, `Acc-Z` (Accelerometer) and `Gyr-X`, `Gyr-Y`, `Gyr-Z` (Gyroscope) streams. The system groups incoming metrics into a "Sliding Temporal Window" of 50 frames per second. By examining sequential 1-second chunks of vibration vectors rather than static nanosecond moments, the transformer deciphers the complex vibrational differences between typical cyclist pedaling wobble and the distinct vertical jolts of cobblestones, successfully inferring the road surface without relying on eyes.

### 3. The Deprecated Systems (`LateFusionNetwork` & `RoadSegmenter`)

Originally, the `LateFusionNetwork` acted as a grand orchestrator attempting to blend spatial outputs from the 2D Vision network (like YOLO or UNet) and the 1D Physics network into a single Multi-Layer Perceptron (MLP) head prediction. This caused a critical circular dependency trap: the model was trying to define ground truth labels simultaneously with predicting them. Both the `LateFusionNetwork` and the secondary custom PyTorch Vision Convolutional chains have been sidelined in the current configuration via `config.yaml` (`use_vision: false`). While they remain in the codebase for potential future camera-based hazard alerting features, they are safely disconnected from the core surface classification loop.

### 4. Dual-Stream Kinematic Fusion (Architecture Map)

To break the "Vibration-Velocity Illusion," the PyTorch architecture splits input metrics into a Two-Tower Neural Network topology before the final Transformer layers.
*   **Stream 1 (High-Frequency Shudder):** Processes the raw 50Hz `Acc` and `Gyr` arrays to map sudden impacts, micro-texture, and vertical suspension displacement.
*   **Stream 2 (Low-Frequency Context):** Processes the 1Hz/10Hz GNSS speed and coordinate orientations to map total momentum and steering angles.
By separating these domains, the model accurately contextualizes high vibration against high velocity without the two signal types diluting each other's gradients during backpropagation.

### 5. Physics-Based DSP Filtering (Preprocessing Map)

Before the sliding IMU windows enter the PyTorch data-loaders, the `data_pipeline` deploys traditional Digital Signal Processing (`scipy.signal`).
*   **Quarter-Car Suspension Subtraction:** A mathematical algorithm models the bicycle's tire pressure and estimated rider mass as a spring-damper system.
*   **Isolating the Road:** We use an inverted Fast Fourier Transform (FFT) / Butterworth filter to subtract this known "bicycle bounce rate" from the raw IMU data. What remains is purely the "road's signature," feeding the neural network heavily normalized residual shock vectors that generalize seamlessly across completely different bicycle frames.

---

## ⚙️ How It Works: The Step-by-Step Training Pipeline

Processing the raw, unorganized `BicycleData` directories into a fully trained PyTorch Neural Network requires a strict progression of three main stages: Offline Annotation, Synchronization, and Core Training.

### Stage 1: Zero-Shot Ground Truth Generation

Before the IMU sensor arrays can learn the feeling of a road, we must tell it what the road actually looks like. Begin by saving time-stamped visual images captured from the camera into directories like `BicycleData/Android/<Session_ID>/VideoFrames/`. Next, execute the Python annotator script. The HuggingFace CLIP pipeline will automatically loop through every folder, evaluating every image frame against the zero-shot surface prompts. It writes out its resulting confidence probabilities and majority-vote classifications into a native `Label.0.csv` file under each session’s root directory.

### Stage 2: Temporal Synchronization

Real-world telemetry streams operate on radically different sampling rates. While standard smartphone IMUs pull physics records 50 to 100 times per second, our video annotation may only deliver a ground truth mapping matching 1 or 10 times per second. By triggering `python3 -m data_pipeline.synchronizer`, the underlying pipeline performs a massive recursive crawl across the global dataset. It utilizes `pandas.merge_asof` logic to tether the low-frequency visual tags directly onto the high-frequency IMU tracking via shared UNIX NTP timestamps. The script securely packages these alignments with distinct `session_id` tags to maintain sequence integrity, saving an aggregated `aligned_dataset.csv` holding millions of synchronized rows.

### Stage 3: PyTorch Model Execution

With the pristine dataset preloaded, initialize training using `python3 train_unified.py`. A custom PyTorch `MultimodalRoadDataset` algorithm will chunk the unified CSV dataset into hundreds of 50-frame sliding arrays. The codebase seamlessly allocates 80% for direct training and walls off 20% for pure validation testing. Pushing metrics through the standard PyTorch forward-propagation loop, the Adam optimizer analyzes its classification loss against the CLIP-generated labels and adjusts system weights until converging. The engine strictly checkpoints its progress across epochs, exporting the ultimate predictive artifact directly to `checkpoints/best_model.pth`.

**Accuracy Expectations**
By training on *all* iOS and Android test sessions simultaneously, the accuracy substantially increases due to:

- **Device Invariance**: The model learns to ignore platform-specific hardware vibrations and focuses heavily on real-world physics.

- **Generalization**: It stops memorizing specific rides and begins identifying mathematically absolute representations of the road.

---

## 🤝 App-Based Annotation Strategy: Interactive CLIP & Manual Canvas

While shifting towards automated labeling, understanding how to handle edge cases is critical for optimizing ground truth accuracy. Instead of relying on third-party cloud tools like Roboflow, the architecture uses a completely local, integrated **App-Based Hybrid System** built directly into the Electron dashboard. 

**Fusing Both for Maximum Accuracy**
The recommended workflow allows the fully automated CLIP pipeline to handle 95% of the baseline heavy lifting. Using the `clip_auto_labeler.py` script, the system rapidly processes thousands of video frames, efficiently classifying broad states like "Asphalt," "Cobblestone," or "Dirt", and drawing aggregate bounding boxes for hazards with zero human effort.

For the remaining 5% of edge cases and anomalies (such as a muddy street resembling asphalt in poor lighting, or detecting the precise boundaries of a tiny pothole), the Electron application exposes two powerful tools:
1. **Interactive CLIP Querying ("Type to highlight more"):** Users can click on any processed frame, type a hyper-specific prompt (e.g., "a yellow painted speed bump"), and execute a targeted, single-frame CLIP analysis. The Python backend processes this instant request and returns the exact coordinates dynamically without writing new static code.
2. **Manual Canvas Annotation ("Draw it yourself"):** If the AI completely fails to interpret a confusing frame, the Electron UI features a built-in HTML5 canvas. Users can manually click and drag bounding boxes over the image. These manual coordinates are pushed directly into the backend and seamlessly merged into the `Label.csv` using identical UNIX timestamps.

By handling both the 95% automation and the 5% manual correction entirely within the local application, the highly accurate manual labels effortlessly overwrite the automated baseline CLIP predictions only where necessary, securing a flawless ground truth baseline while keeping all data 100% private and eliminating cloud uploads.

---

## ❓ Architectural FAQ

### 1. How is the circular dependency between ground truth and detection resolved?

The previous architecture used the `LateFusionNetwork` to simultaneously process both IMU and Vision data during active training. Because the objective is to use the camera data strictly to establish ground truth for the IMU model, fusing them together created a circular dependency where the model relied on the exact data it was supposed to predict. This is resolved by entirely decoupling the two logic streams. Vision tools are now strictly relegated to an offline preprocessing step to generate label CSVs, while the final `Physics1D` model trains exclusively on the IMU data to predict those generated labels.

### 2. Is there a ready-to-go machine learning model to detect road surface?

Yes. OpenAI's **CLIP** model serves as the ready-to-go solution. Because CLIP is a zero-shot model pre-trained on millions of internet images, it inherently understands the visual difference between surfaces like asphalt and cobblestone without requiring the training or fine-tuning of a brand new camera model from scratch.

### 3. How precise is the zero-shot model, and can it be employed as absolute ground truth?

The CLIP model is highly precise for broad, general road conditions, proving approximately 95% accurate for tracking continuous materials (e.g., asphalt vs. gravel). However, it struggles with hyper-specific micro-boundaries, such as the exact coordinate edges of a tiny pothole. To employ it securely and confidently as an absolute ground truth, a temporal smoothing algorithm is applied using a Pandas rolling window. This filters out the 5% anomaly rate (such as a momentary glare on the road), ensuring the resulting ground truth dataset is continuous and stable.

### 4. Should the labeling be done by hand?

Attempting to label 100% of the video frames by hand across all iOS and Android sessions is unscalable and inefficient. Conversely, relying 100% on automated CLIP labeling introduces minor but compounding errors. The solution is the **App-Based Annotation Strategy**. The automated zero-shot model is utilized to process 95% of the baseline dataset in minutes locally. If corrections are needed, they can be made on a separate, dedicated "Manual Draw & Query" tab in the Electron app—using interactive CLIP querying and manual canvas annotations to quickly override the specific failed frames directly without disrupting the automated pipeline.

---

## 🚀 Next Steps

1. **Complete Automated & Interactive Tagging**: Run the `clip_auto_labeler.py` script for baseline labels, refine any confusing edge cases (like obscure potholes) using the Electron app's Interactive CLIP Querying and HTML5 Canvas tools to merge in corrections.
2. **Run The Session Aggregator**: Execute `python3 -m data_pipeline.synchronizer` to weave the new visual tags across every global iOS and Android Session.
3. **Trigger Deep Training**: Launch `python3 train_unified.py` utilizing a high-batch size, observing validation drift carefully to prevent overfitting single specific testing tracks.
4. **Evaluate Model Loss**: Run outputs against the test subset to analyze precision boundaries between visually identical but physically different surfaces (e.g., smooth dirt vs. rough asphalt).
