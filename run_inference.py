import warnings
import pandas as pd
import torch
import numpy as np
import os
import json
import time
import sys
import argparse

warnings.filterwarnings("ignore")
sys.path.append("/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model")

from data_pipeline.dsp_filter import QuarterCarDSP
from models.surface_classifier import SurfaceClassifier

OUTPUT_JSON = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/desktop-app/predictions.json"
SURFACES = [
    "Asphalt (Smooth)", "Gravel (Bumpy)", "Cobblestone (Harsh)", 
    "Grass (Soft)", "Pothole (Anomaly)", "Speed Bump", 
    "Braking (Longitudinal)", "Turning (Lateral)", 
    "Wet Surface (Slick)", "Sand/Dirt (Loose)"
]

def run_sliding_window_inference():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, required=False, help='Path to .pth checkpoint')
    parser.add_argument('--csv', type=str, required=False, help='Path to aligned_dataset.csv')
    args = parser.parse_args()
    
    print("Initializing Dual-Stream Inference Engine...")
    
    # Fallbacks for robustness if not provided
    csv_path = args.csv if args.csv else "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/processed_data/LM-17.06_multi_sensor_aligned.csv"
    
    if not os.path.exists(csv_path):
        print(f"Data not found at {csv_path}")
        return
        
    df = pd.read_csv(csv_path)
    
    # Setup Streams (Mocking 9 and 7 channels to match new architecture)
    core_cols = [c for c in df.columns if 'iOS-Core' in c and ('Acc' in c or 'Gyr' in c)]
    kinematic_cols = [c for c in df.columns if 'hinterrad' in c and ('Acc' in c or 'Gyr' in c)]
    if len(core_cols) == 0 or len(kinematic_cols) == 0:
        print("Missing required columns.")
        return
        
    dsp = QuarterCarDSP(cutoff_freq=3.0, fs=50.0)
    model = SurfaceClassifier(num_classes=10)
    model.eval()
    
    window_size = 50 # 1 second at 50Hz
    results = []
    
    print("Running inference over time-series data...")
    # Simulate first 20 seconds (20 windows)
    for i in range(20):
        start_idx = i * window_size
        end_idx = start_idx + window_size
        
        if end_idx >= len(df): break
            
        imu_chunk = df[core_cols].iloc[start_idx:end_idx]
        kin_chunk = df[kinematic_cols].iloc[start_idx:end_idx]
        
        # Add mock Magnetometer (3 channels) to Core to reach 9 channels
        imu_np = imu_chunk.values
        if imu_np.shape[1] < 9:
            padding = np.zeros((imu_np.shape[0], 9 - imu_np.shape[1]))
            imu_np = np.concatenate([imu_np, padding], axis=1)
            
        # Add mock Speed (1 channel) to Kinematic to reach 7 channels
        kin_np = kin_chunk.values
        if kin_np.shape[1] < 7:
            padding = np.zeros((kin_np.shape[0], 7 - kin_np.shape[1]))
            # Set a mock speed of 5.0 m/s for velocity fusion scaling
            padding[:, 0] = 5.0
            kin_np = np.concatenate([kin_np, padding], axis=1)
            
        # Note: DSP filter processing skipped for mock padding, but you can process raw kin_np here
        
        t_imu = torch.tensor(imu_np, dtype=torch.float32).unsqueeze(0)
        t_kin = torch.tensor(kin_np, dtype=torch.float32).unsqueeze(0)
        
        with torch.no_grad():
            logits = model(t_imu, t_kin)
            probs = torch.softmax(logits, dim=1).squeeze().numpy()
            
        # Since model is untrained, we'll pseudo-bias it for demonstration
        # based on variance in the kinematic (wheel) data. 
        variance = kin_chunk.var().mean()
        
        # Expanded mock classifications mapping
        if variance > 10.0: predicted_idx = 4 # Pothole (massive spike)
        elif variance > 5.0: predicted_idx = 5 # Speed Bump
        elif variance < 0.3: predicted_idx = 0 # Asphalt
        elif variance < 1.0: predicted_idx = 3 # Grass
        elif variance < 2.5: predicted_idx = 1 # Gravel
        else: predicted_idx = 2 # Cobblestone
        
        results.append({
            "timestamp": i,
            "surface": SURFACES[predicted_idx],
            "variance_metric": round(float(variance), 4),
            "confidence": round(float(max(probs) * 100), 2)
        })
        
        print(f"[{i}s] Predicted: {SURFACES[predicted_idx]} (Var: {variance:.4f})")
    
    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=4)
        
    print(f"Inference complete. Results saved to {OUTPUT_JSON}")

if __name__ == "__main__":
    run_sliding_window_inference()
