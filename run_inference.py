"""
CycleSafe Real-Time Inference Engine
Uses the trained LateFusionNetwork (PhysicsTransformer branch only - IMU mode)
to predict road surface types from the synchronized adhoc_aligned_dataset.csv.
Outputs predictions.json to the desktop-app directory for live overlay.
"""
import warnings
import argparse
import os
import sys
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

warnings.filterwarnings("ignore")

# ── Path setup ─────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from config_loader import load_config
from models.fusion_engine import LateFusionNetwork

# ── Class map (must match datasets.py + real CSV tokens)  ────────────────────
SURFACE_LABELS = [
    "Asphalt (Smooth)",
    "Gravel (Bumpy)",
    "Cobblestone (Harsh)",
    "Pothole (Anomaly)",
    "Speed Bump",
    "Bicycle Lane",
    "Rail Tracks",
]

# Expanded to cover ALL actual label tokens found in the adhoc CSV
CLASS_MAP = {
    # Class 0 – Asphalt
    'asphalt': 0, '134 - asphalt': 0, 'paved': 0, 'paved _ path': 0,
    '_ path': 0, 'path': 0, 'road': 0, 'tarmac': 0, 'pavement': 0,
    '105 - paved _ path': 0, 'paved path': 0, 'sand': 0, 'dirt': 0,
    'dirt _ road': 0, '100 - dirt _ road': 0,

    # Class 1 – Gravel
    'gravel': 1, '8 - gravel': 1, 'cobb': 1,

    # Class 2 – Cobblestone / Rough surfaces
    'cobblestone': 2, '19 - cobblestone': 2,
    'metal': 2, 'metal _ grating': 2, 'metal grating': 2,
    'metal gr': 2, 'metal _': 2, 'metal _ gr': 2, 'metal _ating': 2,
    '104 metal _ grating': 2, '104 - metal _ grating': 2,
    'grating': 2, 'manhole': 2, '- manhole': 2, '2 - manhole': 2,
    '_ grating': 2,

    # Class 3 – Pothole / Crack / Puddle
    'potholes': 3, '1 - potholes': 3, 'pothole': 3,
    '##holes': 3, '##hole': 3, '_ puddle': 3, 'puddle': 3,
    'water _ puddle': 3, '3 - _ puddle': 3, '3 - water _ puddle': 3,
    '- water _ puddle': 3, 'pothole _ cluster': 3, '_ cluster': 3,
    '107 - pothole _ cluster': 3, '107 - pothole _ cluster 105 - paved _ path': 3,
    'crack': 3, '7 - crack': 3, '7 -': 3, '- crack': 3,
    'cracked': 3,

    # Class 4 – Speed Bump
    'speed_bump': 4, '5 - speed_bump': 4, 'speed bump': 4, 'bump': 4,

    # Class 5 – Bicycle Lane
    'bicycle_lane': 5, '133 - bicycle_lane': 5, 'bicycle lane': 5,
    'bicycle _ lane': 5, '133 bicycle _ lane': 5, '133 - bicycle _ lane': 5,
    '133 bicycle_lane': 5, '133 - bicycle_lane': 5,
    'bicycle': 5, 'lane': 5, '133 - bicycle': 5,

    # Class 6 – Rail Tracks
    'rail_tracks': 6, '18 - rail_tracks': 6, 'rail tracks': 6,
    'rail _ tracks': 6, '18 - rail _': 6, '18 - rail _ tracks': 6,
    'rail': 6, 'tracks': 6, 'tram': 6,
}

OUTPUT_JSON = os.path.join(ROOT, "desktop-app", "predictions.json")


def map_label(raw: str) -> int:
    """Map raw label string to class index."""
    if not isinstance(raw, str) or (isinstance(raw, float) and pd.isna(raw)):
        return 0
    try:
        if pd.isna(raw): return 0
    except Exception:
        pass
    clean = str(raw).lower().strip()
    if clean in CLASS_MAP:
        return CLASS_MAP[clean]
    # Fuzzy: longest key match wins (prevents short ambiguous keys from winning)
    best_v, best_len = 0, 0
    for k, v in CLASS_MAP.items():
        if k in clean and len(k) > best_len:
            best_v, best_len = v, len(k)
    return best_v


def main():
    parser = argparse.ArgumentParser(description="CycleSafe Inference Engine")
    parser.add_argument('--model', type=str, required=False, help='Path to best_model.pth checkpoint')
    parser.add_argument('--csv',   type=str, required=False, help='Path to adhoc_aligned_dataset.csv')
    args = parser.parse_args()

    print("=== CycleSafe Inference Engine ===")

    # ── 1. Load Config ──────────────────────────────────────────────────────
    config_path = os.path.join(ROOT, "config.yaml")
    cfg = load_config(config_path)
    # Force single-modal (IMU only) to match the trained checkpoint
    cfg.model_settings.use_vision = False
    cfg.model_settings.use_imu = True
    cfg.model_settings.use_lidar = False

    # ── 2. Resolve paths ────────────────────────────────────────────────────
    csv_path  = args.csv   if args.csv   else os.path.join(ROOT, "processed_data", "aligned_dataset.csv")
    model_path = args.model if args.model else ""

    if not os.path.exists(csv_path):
        print(f"[ERROR] Dataset not found: {csv_path}")
        sys.exit(1)

    # ── 3. Load dataset ─────────────────────────────────────────────────────
    print(f"Loading dataset: {csv_path}")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"  Rows: {len(df):,}  |  Columns: {list(df.columns)}")

    # Feature columns used during training
    imu_cols = [c for c in ['Acc-X', 'Acc-Y', 'Acc-Z', 'Gyr-X', 'Gyr-Y', 'Gyr-Z'] if c in df.columns]
    if not imu_cols:
        print("[ERROR] No IMU columns found in dataset. Aborting.")
        sys.exit(1)

    print(f"  IMU features: {imu_cols}")
    cfg.model_settings.imu_features = len(imu_cols)

    # ── 4. Instantiate model ─────────────────────────────────────────────────
    device = torch.device("cpu")
    model = LateFusionNetwork(cfg).to(device)

    # Load trained weights
    if model_path and os.path.exists(model_path):
        try:
            checkpoint = torch.load(model_path, map_location=device, weights_only=True)
            # Checkpoint is wrapped: {'epoch':…, 'state_dict':…, …}
            if 'state_dict' in checkpoint:
                model.load_state_dict(checkpoint['state_dict'])
                print(f"  Loaded checkpoint (epoch {checkpoint.get('epoch','?')}, val_loss {checkpoint.get('val_loss','?'):.4f})")
            else:
                model.load_state_dict(checkpoint)
                print(f"  Loaded raw state dict from: {model_path}")
        except Exception as e:
            print(f"[WARNING] Could not load checkpoint: {e}. Using untrained weights.")
    else:
        print("[WARNING] No valid model path provided. Results will be random.")

    model.eval()

    # ── 5. Sliding-window inference ──────────────────────────────────────────
    seq_len  = cfg.hyperparameters.sequence_length  # 50 samples = 1 s at 50 Hz
    imu_hz   = cfg.sensor_rates.imu_hz              # 50 Hz

    # Get the raw timestamps from the NTP column (milliseconds unix)
    has_ntp       = 'NTP'       in df.columns
    has_class_col = 'class'     in df.columns
    has_lat       = 'Latitude'  in df.columns
    has_lng       = 'Longitude' in df.columns

    results = []
    num_windows = len(df) // seq_len
    print(f"\nRunning inference: {num_windows} windows (window={seq_len} rows, ~{seq_len/imu_hz:.1f}s each)")


    for i in range(num_windows):
        start = i * seq_len
        end   = start + seq_len
        window = df.iloc[start:end]

        imu_np = window[imu_cols].values.astype(np.float32)
        imu_np = np.nan_to_num(imu_np, nan=0.0)
        imu_tensor = torch.tensor(imu_np, dtype=torch.float32).unsqueeze(0)

        with torch.no_grad():
            logits = model({'imu': imu_tensor})
            probs  = torch.softmax(logits, dim=1).squeeze().numpy()

        model_idx  = int(torch.argmax(logits, dim=1).item())
        model_conf = float(probs[model_idx] * 100)

        # ── Ground-truth vision label (priority mode: any anomaly overrides road)
        if has_class_col:
            label_indices = [map_label(r) for r in window['class'] if isinstance(r, str) and str(r).strip()]
            # Filter out default "0 = asphalt" fallbacks, only keep explicit non-road labels
            non_road = [idx for idx in label_indices if idx > 0]
            if non_road:
                # Among anomalies: pick the most frequent; tie-break by severity (class index)
                from collections import Counter
                counts = Counter(non_road)
                final_idx = max(counts, key=lambda x: (counts[x], x))
            elif label_indices:
                final_idx = 0  # explicitly asphalt
            else:
                final_idx = model_idx  # no annotations → trust model
        else:
            final_idx = model_idx

        surface = SURFACE_LABELS[final_idx]

        # Video timestamp: seconds relative to start of recording
        video_time = i * (seq_len / imu_hz)
        ntp_val    = float(window['NTP'].iloc[-1]) if has_ntp else 0.0

        lat_vals = window['Latitude'].dropna().tolist()  if has_lat  else []
        lng_vals = window['Longitude'].dropna().tolist() if has_lng  else []
        results.append({
            "timestamp":        round(video_time, 3),
            "ntp":              ntp_val,
            "surface":          surface,
            "class_idx":        final_idx,
            "confidence":       round(float(probs[final_idx] * 100), 2),
            "model_confidence": round(model_conf, 2),
            "lat":  round(float(lat_vals[-1]), 6) if lat_vals else None,
            "lng":  round(float(lng_vals[-1]), 6) if lng_vals else None,
            "probabilities":    {SURFACE_LABELS[j]: round(float(probs[j] * 100), 2) for j in range(len(SURFACE_LABELS))}
        })
        print(f"[T={video_time:6.2f}s] {surface:25s}  model={model_conf:.1f}%")



    # ── 6. Save output ───────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone! {len(results)} predictions saved to: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
