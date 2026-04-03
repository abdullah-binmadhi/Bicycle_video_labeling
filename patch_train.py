import re

file_path = 'train_unified.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Update parser
parser_search = """    parser = argparse.ArgumentParser(description="Unified PyTorch Training.")
    parser.add_argument("--dataset", type=str, help="Path to the aligned dataset CSV", default="")
    args = parser.parse_args()"""

parser_replace = """    parser = argparse.ArgumentParser(description="Unified PyTorch Training.")
    parser.add_argument("--dataset", type=str, help="Path to the aligned dataset CSV", default="")
    parser.add_argument("--epochs", type=int, help="Override number of epochs", default=None)
    parser.add_argument("--lr", type=float, help="Override learning rate", default=None)
    parser.add_argument("--batch_size", type=int, help="Override batch size", default=None)
    parser.add_argument("--checkpoint", type=str, help="Path to a .pth checkpoint to resume from", default="")
    parser.add_argument("--use_vision", action="store_true", help="Enable vision parameters")
    parser.add_argument("--use_imu", action="store_true", help="Enable IMU parameters")
    args = parser.parse_args()"""

text = text.replace(parser_search, parser_replace)

# Update config modifications
config_search = """    # 2. Prepare Data
    if args.dataset:"""

config_replace = """    # Dynamic Overrides from UI
    if args.epochs is not None: cfg.hyperparameters.epochs = args.epochs
    if args.lr is not None: cfg.hyperparameters.learning_rate = args.lr
    if args.batch_size is not None: cfg.hyperparameters.batch_size = args.batch_size

    # 2. Prepare Data
    if args.dataset:"""

text = text.replace(config_search, config_replace)

# Update LateFusionNetwork loading
init_search = """    model = LateFusionNetwork(cfg).to(device)
    logging.info("Initialized LateFusionNetwork.")

    # 4. Optimizer Selection
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg.hyperparameters.learning_rate)"""

init_replace = """    model = LateFusionNetwork(cfg).to(device)
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
        logging.info(f"Resumed from epoch {start_epoch}")"""

text = text.replace(init_search, init_replace)

# Update loop
loop_search = """    for epoch in range(num_epochs):
        print(f"\\n[{epoch+1}/{num_epochs}]")"""

loop_replace = """    for epoch in range(start_epoch, num_epochs):
        print(f"\\n[{epoch+1}/{num_epochs}]")"""

text = text.replace(loop_search, loop_replace)

# JSON stdout
stats_search = """        is_best = val_loss < best_val_loss
        if is_best:
            best_val_loss = val_loss"""

stats_replace = """        is_best = val_loss < best_val_loss
        if is_best:
            best_val_loss = val_loss
            
        import json
        print(f"EPOCH_STATS:{json.dumps({'epoch': epoch + 1, 'train_loss': train_loss, 'val_loss': val_loss})}")"""

text = text.replace(stats_search, stats_replace)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
print("train_unified.py patched successfully")
