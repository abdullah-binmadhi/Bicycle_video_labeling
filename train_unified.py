import os
import sys
import torch
import argparse
import logging
from pathlib import Path

# Fix relative imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tqdm import tqdm
from torch.utils.data import DataLoader, random_split

# Project modules
from config_loader import load_config
from data_pipeline.datasets import MultimodalRoadDataset
from models.fusion_engine import LateFusionNetwork
# Note: For pure 1D processing, or isolated vision testing, you can dynamically 
# instantiate PhysicsTransformer or RoadSegmenter instead of the LateFusionNetwork.

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def save_checkpoint(state: dict, is_best: bool, checkpoint_dir: Path, filename: str = 'checkpoint.pth'):
    """Saves the current model state. If best, saves a dedicated best_model.pth."""
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    filepath = checkpoint_dir / filename
    torch.save(state, filepath)
    if is_best:
        best_filepath = checkpoint_dir / 'best_model.pth'
        torch.save(state, best_filepath)
        logging.info(f"--> Saved new BEST model with Val Loss: {state.get('val_loss', 'N/A'):.4f}")

def train_epoch(model: torch.nn.Module, dataloader: DataLoader, optimizer: torch.optim.Optimizer, device: torch.device) -> float:
    """Trains the model for one complete epoch."""
    model.train()
    running_loss = 0.0
    
    # DevEx: Wraps generic DataLoader with tqdm progress bar
    pbar = tqdm(dataloader, desc="Training")
    for batch in pbar:
        # Move inputs to target device (GPU/CPU)
        x_dict = {}
        for key, tensor in batch.items():
            if key != 'label':
                x_dict[key] = tensor.to(device)
        
        targets = batch['label'].to(device)
        
        # Zero gradients
        optimizer.zero_grad()
        
        # Forward Pass
        outputs = model(x_dict)
        
        # Calculate Loss using strictly defined OOP contract
        loss = model.calculate_loss(outputs, targets)
        
        # Backward Pass & Optimize
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()
        pbar.set_postfix({'loss': f"{loss.item():.4f}"})
        
    avg_loss = running_loss / len(dataloader)
    return avg_loss

def validate_epoch(model: torch.nn.Module, dataloader: DataLoader, device: torch.device) -> float:
    """Evaluates the model without gradient tracking."""
    model.eval()
    running_loss = 0.0
    
    pbar = tqdm(dataloader, desc="Validation", leave=False)
    with torch.no_grad():
        for batch in pbar:
            x_dict = {}
            for key, tensor in batch.items():
                if key != 'label':
                    x_dict[key] = tensor.to(device)
                    
            targets = batch['label'].to(device)
            
            outputs = model(x_dict)
            loss = model.calculate_loss(outputs, targets)
            
            running_loss += loss.item()
            pbar.set_postfix({'val_loss': f"{loss.item():.4f}"})
            
    avg_loss = running_loss / len(dataloader)
    return avg_loss

def main():
    """Master executor routing config, data, model, and the training loop."""
    parser = argparse.ArgumentParser(description="Unified PyTorch Training.")
    parser.add_argument("--dataset", type=str, help="Path to the aligned dataset CSV", default="")
    args = parser.parse_args()

    # 1. Load Configurations
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
    cfg = load_config(config_path)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    logging.info(f"Using compute device: {device}")
    
    # 2. Prepare Data
    if args.dataset:
        csv_path = Path(args.dataset)
    else:
        # Assume synchronizer.py has been run and placed data here:
        csv_path = Path(cfg.data_paths.processed_dir) / "aligned_dataset.csv"
        
    logging.info(f"Loading dataset from: {csv_path}")
    
    # Feature columns matching the Bicycle CycleSafe data
    feature_columns = ['Acc-X', 'Acc-Y', 'Acc-Z', 'Gyr-X', 'Gyr-Y', 'Gyr-Z']
    
    try:
        full_dataset = MultimodalRoadDataset(
            csv_path=csv_path,
            config=cfg,
            feature_cols=feature_columns,
            label_col='Label' # Updated to match paper UI nomenclature
        )
    except FileNotFoundError:
        logging.error(f"Cannot start training! '{csv_path}' missing. Run data_pipeline/synchronizer.py first.")
        return

    # Split dataset 80/20 for Train/Validation
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=cfg.hyperparameters.batch_size, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_dataset, batch_size=cfg.hyperparameters.batch_size, shuffle=False, num_workers=4)

    # 3. Instantiate Dynamically Routed Model
    # Leveraging the Fusion Engine config-driven logic
    model = LateFusionNetwork(cfg).to(device)
    logging.info("Initialized LateFusionNetwork.")

    # 4. Optimizer Selection
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg.hyperparameters.learning_rate)

    # 5. Execute Epochs
    best_val_loss = float('inf')
    num_epochs = cfg.hyperparameters.epochs
    checkpoint_dir = Path("checkpoints")
    
    logging.info("Starting robust training loop...")
    for epoch in range(num_epochs):
        print(f"\n[{epoch+1}/{num_epochs}]")
        
        train_loss = train_epoch(model, train_loader, optimizer, device)
        val_loss = validate_epoch(model, val_loader, device)
        
        logging.info(f"Epoch {epoch+1} Summary - Train Loss: {train_loss:.4f} | Validation Loss: {val_loss:.4f}")
        
        # Checkpointing logic
        is_best = val_loss < best_val_loss
        if is_best:
            best_val_loss = val_loss
            
        save_checkpoint({
            'epoch': epoch + 1,
            'state_dict': model.state_dict(),
            'val_loss': val_loss,
            'optimizer': optimizer.state_dict(),
        }, is_best, checkpoint_dir)

if __name__ == "__main__":
    main()
