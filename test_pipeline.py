import warnings
import pandas as pd
import torch
import numpy as np
import os
import sys

warnings.filterwarnings("ignore")
sys.path.append("/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model")

from data_pipeline.dsp_filter import QuarterCarDSP
from models.dual_stream import DualStreamPhysicsTransformer

CSV_PATH = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/processed_data/LM-17.06_multi_sensor_aligned.csv"

def run_test():
    print("------------------------------------------")
    print("[1] Loading Synchronized LM-17.06 Dataset")
    if not os.path.exists(CSV_PATH):
        print(f"File not found: {CSV_PATH}")
        return
        
    df = pd.read_csv(CSV_PATH, nrows=500) # Load 500 rows for sequence test
    print(f"Loaded {len(df)} rows. Columns: {len(df.columns)}")
    
    print("\n[2] Separating Streams (Core vs Suspension)")
    core_cols = [c for c in df.columns if 'iOS-Core' in c and ('Acc' in c or 'Gyr' in c)]
    kinematic_cols = [c for c in df.columns if 'hinterrad' in c and ('Acc' in c or 'Gyr' in c)]
    
    imu_df = df[core_cols]
    kinematic_df = df[kinematic_cols]
    
    print(f"  -> IMU Columns (Stream 1): {list(imu_df.columns)}")
    print(f"  -> Kinematic Columns (Stream 2): {list(kinematic_df.columns)}")
    
    print("\n[3] Applying Quarter-Car DSP Filter to Kinematic Stream")
    dsp = QuarterCarDSP(cutoff_freq=3.0, fs=50.0)
    
    # We apply the filter only to kinematic data
    kinematic_filtered_df = dsp.process_dataframe(kinematic_df)
    
    print("  -> High-pass filtering completed (Bicycle frame-bounce removed).")
    
    print("\n[4] Converting to Tensors [Batch=1, SeqLen=500, Features=6]")
    # Expand dims to add Batch dimension
    t_imu = torch.tensor(imu_df.values, dtype=torch.float32).unsqueeze(0) 
    t_kinematic = torch.tensor(kinematic_filtered_df.values, dtype=torch.float32).unsqueeze(0)
    
    print(f"  -> IMU Tensor Shape: {t_imu.shape}")
    print(f"  -> Kinematic Tensor Shape: {t_kinematic.shape}")
    
    print("\n[5] Passing Data into Dual-Stream Physics Transformer")
    model = DualStreamPhysicsTransformer(
        imu_input_size=len(core_cols), 
        kinematic_input_size=len(kinematic_cols), 
        d_model=64
    )
    
    model.eval()
    with torch.no_grad():
        output = model(t_imu, t_kinematic)
        
    print("\n[✔] TEST SUCCESSFUL!")
    print(f"Model Output Embedding Shape: {output.shape} (Ready for Classification Head)")
    print("------------------------------------------")

if __name__ == "__main__":
    run_test()
