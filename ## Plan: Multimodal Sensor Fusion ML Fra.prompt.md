## Plan: Multimodal Sensor Fusion ML Framework

A unified, modular PyTorch-based Machine Learning framework designed to initially process 1D Bicycle sensor data (IMU, GNSS) while providing a robust architectural foundation for future 2D (Video) and 3D (LIDAR) modalities. Built with strict object-oriented patterns to support a future SDK release.

**Steps**
1. **Configuration System**: Set up `config.yaml` with explicit boolean flags for modalities (e.g., `use_vision: false`, `use_imu: true`). Implement `config_loader.py` using standard Python `dataclasses` to parse YAML for strict type hinting and IDE support.
2. **Data Synchronization Engine**: Implement `data_pipeline/synchronizer.py`. Use the 100Hz IMU timeline as the base. Align GNSS and other low-frequency 1D sensors using `pandas.merge_asof` with backward direction and defined tolerance. Add interpolation for dropping frames.
3. **Dataset Definition**: Develop `data_pipeline/datasets.py` (`MultimodalRoadDataset`). Build dynamic loading logic that checks config flags and yields `(sensor_sequence, label)` tensors initially, and seamlessly integrates `(image_tensor, sensor_sequence, label)` later.
4. **Base Model Infrastructure**: Create `models/base_model.py` with `BaseRoadModel` (inherits `nn.Module` and `abc.ABC`). Enforce `forward`, `calculate_loss`, and `predict` interfaces.
5. **Physics/1D Model Implementation**: Implement `models/physics_1d.py`. Build a 1D-CNN or LSTM designed explicitly to extract temporal features from the synced tabular sensor data.
6. **Vision Modality Stubs**: Create `models/vision_2d.py` with placeholder wrappers for YOLO and U-Net that conform to `BaseRoadModel`, ensuring future drop-in compatibility.
7. **Fusion Engine Integration**: Implement `models/fusion_engine.py`. Design a dynamic forward pass that checks available features. If only `physics_features` are available, pass directly to the classification MLP. If `vision_features` exist, concatenate before MLP.
8. **Unified Training Loop**: Write `train_unified.py` with `tqdm` progress bars, dynamic loss routing based on task configuration, and strictly validation-driven checkpointing.

**Relevant files**
- `config.yaml` & `config_loader.py` — Config management and typing.
- `data_pipeline/synchronizer.py` — Pandas alignment logic.
- `data_pipeline/datasets.py` — PyTorch Dataset for multimodal sequence packing.
- `models/base_model.py` — ABC interface enforcing model structure.
- `models/physics_1d.py` — LSTM/1D-CNN for current Bicycle sensor data.
- `models/fusion_engine.py` — Dynamic late-fusion architecture.
- `train_unified.py` — Master training loop.

**Verification**
1. Run `python config_loader.py` to assert valid dataclass instantiation.
2. Run `pytest` on `synchronizer.py` with a dummy CSV to verify `merge_asof` alignment and absence of nulls.
3. Instantiate `MultimodalRoadDataset` and assert the shape of output batches (e.g., `[Batch, Seq_Len, Features]`).
4. Perform a dry-run of `train_unified.py` for 2 epochs on a small subset of the 1D data to verify loss convergence and checkpoint saving.

**Decisions**
- **Graceful Degradation:** The Fusion Engine is designed to dynamically accept whatever tensors `MultimodalRoadDataset` yields. Right now, Vision is disabled, so the MLP trains purely on the IMU representation.
- **Future-proofing for SDK:** Strict type hinting and `BaseRoadModel` inheritance ensure that when you package this as an SDK, users can inject custom PyTorch models by inheriting the ABC.

**Further Considerations**
1. To align the IMU data properly, do you have a preferred absolute timestamp format (e.g., milliseconds since epoch) in your sensor CSVs?
2. Shall we initially design the 1D model as a simple 1D-CNN for computational efficiency, or an LSTM for stronger temporal memory?
