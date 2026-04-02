import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings("ignore")
import sys
sys.path.append("/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model")

from models.surface_classifier import SurfaceClassifier
from data_pipeline.dsp_filter import QuarterCarDSP

CSV_PATH = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/processed_data/LM-17.06_multi_sensor_aligned.csv"
WEIGHTS_DIR = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/weights"
os.makedirs(WEIGHTS_DIR, exist_ok=True)

class BicycleSurfaceDataset(Dataset):
    def __init__(self, csv_filepath, window_size=50, dsp_filter=None):
        self.df = pd.read_csv(csv_filepath)
        self.window_size = window_size
        self.dsp = dsp_filter
        
        self.core_cols = [c for c in self.df.columns if 'iOS-Core' in c and ('Acc' in c or 'Gyr' in c)]
        self.kin_cols = [c for c in self.df.columns if 'hinterrad' in c and ('Acc' in c or 'Gyr' in c)]
        
        # Calculate valid num windows
        self.num_windows = len(self.df) // self.window_size
        
        print(f"Dataset initialized with {self.num_windows} samples (window={window_size})")

    def __len__(self):
        return self.num_windows

    def __getitem__(self, idx):
        start = idx * self.window_size
        end = start + self.window_size
        
        imu_chunk = self.df[self.core_cols].iloc[start:end].values
        kin_chunk = self.df[self.kin_cols].iloc[start:end].copy()
        
        # Apply DSP filter to the kinematic variables directly in dataloader
        if self.dsp is not None:
            kin_chunk = self.dsp.process_dataframe(kin_chunk)
            kin_chunk = kin_chunk.values
        else:
            kin_chunk = kin_chunk.values
            
        # For training, we need ground-truth labels. Since we do not have manual video annotations yet,
        # we will pseudo-annotate based on the kinematic suspension vibration (variance heuristics)
        # to teach the fusion model how to recognize the patterns automatically.
        variance = np.var(kin_chunk)
        if variance < 0.3: label = 0 # Asphalt
        elif variance < 1.0: label = 3 # Grass
        elif variance < 2.5: label = 1 # Gravel
        else: label = 2 # Cobblestone
            
        imu_tensor = torch.tensor(imu_chunk, dtype=torch.float32)
        kin_tensor = torch.tensor(kin_chunk, dtype=torch.float32)
        label_tensor = torch.tensor(label, dtype=torch.long)
        
        return imu_tensor, kin_tensor, label_tensor

def train_model():
    print("=============================================")
    print("Initiating Dual-Stream Tensor Optimization")
    print("=============================================")
    
    # Setup Device
    device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
    print(f"Accelerating on: {device}")
    
    # Load Tools
    dsp = QuarterCarDSP(cutoff_freq=3.0, fs=50.0)
    dataset = BicycleSurfaceDataset(CSV_PATH, window_size=50, dsp_filter=dsp)
    
    # 80/20 Train-Val Split
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
    
    # Init Model
    model = SurfaceClassifier(num_classes=4).to(device)
    
    # Loss & Optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4) # Adam with Weight Decay
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=2, factor=0.5)
    
    epochs = 15
    best_val_loss = float('inf')
    
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        for imu, kin, labels in train_loader:
            imu, kin, labels = imu.to(device), kin.to(device), labels.to(device)
            
            optimizer.zero_grad()
            
            outputs = model(imu, kin)
            loss = criterion(outputs, labels)
            
            loss.backward()
            
            # gradient clipping to prevent exploding gradients
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            
            optimizer.step()
            
            running_loss += loss.item() * imu.size(0)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
        epoch_loss = running_loss / len(train_dataset)
        epoch_acc = 100 * correct / total
        
        # Validation
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for imu, kin, labels in val_loader:
                imu, kin, labels = imu.to(device), kin.to(device), labels.to(device)
                outputs = model(imu, kin)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item() * imu.size(0)
                _, predicted = torch.max(outputs.data, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()
                
        val_loss = val_loss / len(val_dataset)
        val_acc = 100 * val_correct / val_total
        scheduler.step(val_loss)
        
        print(f"Epoch [{epoch+1}/{epochs}] | Train Loss: {epoch_loss:.4f}, Acc: {epoch_acc:.1f}% | Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.1f}%")
        
        # Snapshot best weights
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            weights_path = os.path.join(WEIGHTS_DIR, "dual_stream_best.pth")
            torch.save(model.state_dict(), weights_path)
            
    print("=============================================")
    print(f"Optimization Complete! Best weights saved to: {weights_path}")
    print("Models converged, Meta-Fusion matrices are primed.")

if __name__ == "__main__":
    train_model()
