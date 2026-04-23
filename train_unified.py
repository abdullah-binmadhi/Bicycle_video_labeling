import os
import sys
import json
import torch
import argparse
import logging
from pathlib import Path
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

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

def validate_epoch(model: torch.nn.Module, dataloader: DataLoader, device: torch.device):
    """Evaluates the model without gradient tracking."""
    model.eval()
    running_loss = 0.0
    all_targets = []
    all_preds = []
    
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
            
            # Assuming outputs are logits, get predictions
            preds = torch.argmax(outputs, dim=1) if len(outputs.shape) > 1 else (outputs > 0.5).long()
            all_targets.extend(targets.cpu().numpy())
            all_preds.extend(preds.cpu().numpy())
            
    avg_loss = running_loss / len(dataloader)
    return avg_loss, all_targets, all_preds

def validate_master_annotations(csv_path: Path) -> bool:
    """
    Pre-flight check for master_annotations.csv before training.
    Validates schema, coordinate sanity, and label integrity.
    Returns True if file is valid, False if critical errors found.
    """
    import pandas as pd
    required_cols = {'image_id', 'label_code', 'class_name', 'xmin', 'ymin', 'xmax', 'ymax', 'score'}

    if not csv_path.exists():
        logging.warning(f"[Validation] master_annotations.csv not found at {csv_path}. Skipping annotation check.")
        return True  # Not fatal — training can proceed without manual annotations

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        logging.error(f"[Validation] Cannot parse master_annotations.csv: {e}")
        return False

    # Check schema
    missing = required_cols - set(df.columns.str.lower())
    if missing:
        logging.error(f"[Validation] master_annotations.csv missing columns: {missing}")
        return False

    total = len(df)
    errors = []

    # Check coordinate sanity
    bad_coords = df[(df['xmin'] >= df['xmax']) | (df['ymin'] >= df['ymax'])]
    if len(bad_coords):
        errors.append(f"{len(bad_coords)} rows with invalid bbox (xmin>=xmax or ymin>=ymax)")

    # Check for NaN in critical columns
    nan_rows = df[['xmin', 'ymin', 'xmax', 'ymax', 'score']].isnull().any(axis=1).sum()
    if nan_rows:
        errors.append(f"{nan_rows} rows with NaN in coordinate or score columns")

    # Check label_code is numeric
    non_numeric = df[pd.to_numeric(df['label_code'], errors='coerce').isna()]
    if len(non_numeric):
        errors.append(f"{len(non_numeric)} rows with non-numeric label_code")

    # Check score range
    invalid_score = df[(df['score'] < 0) | (df['score'] > 1)]
    if len(invalid_score):
        errors.append(f"{len(invalid_score)} rows with score outside [0, 1]")

    if errors:
        logging.warning(f"[Validation] master_annotations.csv — {total} total rows, issues found:")
        for err in errors:
            logging.warning(f"  ⚠  {err}")
        logging.warning("[Validation] Annotation issues detected. Training will continue but review your annotation data.")
    else:
        logging.info(f"[Validation] ✅ master_annotations.csv passed all checks ({total} rows, schema valid).")

    return True  # Warn but don't block training — errors are non-fatal


def main():
    """Master executor routing config, data, model, and the training loop."""
    parser = argparse.ArgumentParser(description="Unified PyTorch Training.")
    parser.add_argument("--dataset", type=str, help="Path to the aligned dataset CSV", default="")
    parser.add_argument("--epochs", type=int, help="Override number of epochs", default=None)
    parser.add_argument("--lr", type=float, help="Override learning rate", default=None)
    parser.add_argument("--batch_size", type=int, help="Override batch size", default=None)
    parser.add_argument("--checkpoint", type=str, help="Path to a .pth checkpoint to resume from", default="")
    parser.add_argument("--use_vision", action="store_true", help="Enable vision parameters")
    parser.add_argument("--use_imu", action="store_true", help="Enable IMU parameters")
    parser.add_argument("--output_dir", type=str, help="Output directory to save checkpoints", default="checkpoints")
    parser.add_argument("--annotations", type=str, help="Path to master_annotations.csv to validate", default="")
    args = parser.parse_args()

    # 0. Pre-flight: Validate master_annotations.csv if present
    annotations_path = Path(args.annotations) if args.annotations else Path("desktop-app/master_annotations.csv")
    if not validate_master_annotations(annotations_path):
        logging.error("Annotation validation failed critically. Fix master_annotations.csv before training.")
        return

    # 1. Load Configurations
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
    cfg = load_config(config_path)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    logging.info(f"Using compute device: {device}")
    
    # Dynamic Overrides from UI
    if args.epochs is not None: cfg.hyperparameters.epochs = args.epochs
    if args.lr is not None: cfg.hyperparameters.learning_rate = args.lr
    if args.batch_size is not None: cfg.hyperparameters.batch_size = args.batch_size

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
            label_col='class_name' # Updated to match OWLv2 output class col
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

    start_epoch = 0
    if args.checkpoint and os.path.exists(args.checkpoint):
        logging.info(f"Loading checkpoint {args.checkpoint}")
        checkpoint = torch.load(args.checkpoint, map_location=device)
        model.load_state_dict(checkpoint['state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer'])
        start_epoch = checkpoint.get('epoch', 0)
        logging.info(f"Resumed from epoch {start_epoch}")

    # 5. Execute Epochs
    best_val_loss = float('inf')
    num_epochs = cfg.hyperparameters.epochs
    
    if args.output_dir == "checkpoints":
        checkpoint_dir = Path("checkpoints")
    elif args.output_dir.endswith("checkpoints"):
        checkpoint_dir = Path(args.output_dir)
    else:
        checkpoint_dir = Path(args.output_dir) / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    logging.info("Starting robust training loop...")
    history = {'epochs': [], 'train_loss': [], 'val_loss': []}
    for epoch in range(start_epoch, num_epochs):
        print(f"\n[{epoch+1}/{num_epochs}]")
        
        train_loss = train_epoch(model, train_loader, optimizer, device)
        val_loss, all_targets, all_preds = validate_epoch(model, val_loader, device)
        
        logging.info(f"Epoch {epoch+1} Summary - Train Loss: {train_loss:.4f} | Validation Loss: {val_loss:.4f}")
        
        # Calculate specialized metrics
        acc = accuracy_score(all_targets, all_preds)
        f1 = f1_score(all_targets, all_preds, average='weighted', zero_division=0)
        import warnings
        from sklearn.exceptions import UndefinedMetricWarning
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)
            cm = confusion_matrix(all_targets, all_preds, labels=list(range(cfg.model_settings.num_classes))).tolist()
        
        history['epochs'].append(epoch + 1)
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)

        metrics_dict = {
            'epoch': epoch + 1,
            'train_loss': train_loss,
            'val_loss': val_loss,
            'accuracy': acc,
            'f1_score': f1,
            'confusion_matrix': cm,
            'history': history,
            'temporal_stability': [f1] * max(1, epoch) # mock flicker until implemented via tracking
        }
        
        # Checkpointing logic
        is_best = val_loss < best_val_loss
        if is_best:
            best_val_loss = val_loss
            
            # Ensure the directory exists before saving metrics
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            
        print(f"EPOCH_STATS:{json.dumps(metrics_dict)}")
            
        save_checkpoint({
            'epoch': epoch + 1,
            'state_dict': model.state_dict(),
            'val_loss': val_loss,
            'optimizer': optimizer.state_dict(),
        }, is_best, checkpoint_dir)

if __name__ == "__main__":
    main()
