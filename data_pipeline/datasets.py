import logging
import cv2
import torch
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from torch.utils.data import Dataset
from torchvision import transforms as T
from PIL import Image

# Ensure config_loader is accessible. Assuming this is run from the project root.
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config_loader import FrameworkConfig

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

class MultimodalRoadDataset(Dataset):
    """
    A unified PyTorch Dataset for loading synchronized multimodal sensor and video data.
    
    This dataset uses a sliding window approach to extract temporal sequences of 1D 
    sensor data (e.g., IMU) and dynamically pairs it with corresponding Video or LIDAR 
    frames if enabled via the system configuration.
    
    Attributes:
        data_df (pd.DataFrame): The temporally aligned master dataframe.
        config (FrameworkConfig): Configuration dictating activated modalities.
        seq_len (int): Temporal window size for 1D sensors.
        feature_cols (List[str]): Columns representing the IMU/1D features.
        label_col (str): The column containing the target class.
        vision_transform (T.Compose): PyTorch vision transformations.
    """

    def __init__(self, 
                 csv_path: str | Path, 
                 config: FrameworkConfig, 
                 feature_cols: List[str], 
                 label_col: str = "Label",
                 image_path_col: str = "image_path",
                 stride: int = 1,
                 vision_transform: Optional[T.Compose] = None):
        """
        Initializes the multimodal dataset.

        Args:
            csv_path (str | Path): Path to the aligned master CSV from synchronizer.
            config (FrameworkConfig): Architecture features and pathways config.
            feature_cols (List[str]): List of column names to extract as physical features.
            label_col (str): Column name containing the ground truth label.
            image_path_col (str): Column name containing relative paths to image frames.
            stride (int): Step size for extracting sliding windows (reduces overlap if > 1).
            vision_transform (Optional[T.Compose]): Transformations for the vision branch.
        """
        self.config = config
        self.seq_len = config.hyperparameters.sequence_length
        self.feature_cols = feature_cols
        self.label_col = label_col
        self.image_path_col = image_path_col
        self.base_dir = Path(config.data_paths.sensor_data_dir).parent
        
        # Load the synchronized dataset
        try:
            self.data_df = pd.read_csv(csv_path)
            # Ensure the necessary columns exist
            missing_cols = [c for c in feature_cols + [label_col] if c not in self.data_df.columns]
            if missing_cols:
                raise ValueError(f"Missing expected columns in CSV: {missing_cols}")
        except FileNotFoundError:
            logging.error(f"Failed to find aligned dataset at {csv_path}")
            raise
        
        # Pre-compute valid starting indices for the sliding window
        # Max index is len(df) - seq_len per session
        if len(self.data_df) < self.seq_len:
            raise ValueError(f"Dataset length ({len(self.data_df)}) is shorter than sequence length ({self.seq_len})")
            
        self.valid_indices = []
        if 'session_id' in self.data_df.columns:
            for session, group in self.data_df.groupby('session_id'):
                start_row = group.index[0]
                end_row = group.index[-1]
                num_valid_in_session = len(group) - self.seq_len + 1
                if num_valid_in_session > 0:
                    session_indices = list(range(start_row, start_row + num_valid_in_session, stride))
                    self.valid_indices.extend(session_indices)
        else:
            # Fallback to standard range if no session id exists
            self.valid_indices = list(range(0, len(self.data_df) - self.seq_len + 1, stride))
        
        # Setup Vision Transforms dynamically
        self.vision_transform = vision_transform or self._get_default_transforms()
        
        logging.info(f"Initialized Multimodal Dataset: {len(self.valid_indices)} samples available.")
        logging.info(f"- Vision Enabled: {self.config.model_settings.use_vision}")
        logging.info(f"- IMU Enabled: {self.config.model_settings.use_imu}")

    def _get_default_transforms(self) -> T.Compose:
        """
        Provides consistent default data augmentations and normalization for vision.
        
        Returns:
            T.Compose: Standard ResNet/ImageNet normalization pipeline.
        """
        return T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            # Standard ImageNet normalization coefficients
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def load_image(self, rel_path: str) -> Optional[torch.Tensor]:
        """
        Safely loads an image frame from disk and applies transformations.

        Args:
            rel_path (str): Relative image file path from the CSV.

        Returns:
            Optional[torch.Tensor]: The transformed image tensor, or None if failed.
        """
        # Resolve path relative to where datasets are stored
        full_path = self.base_dir / str(rel_path)
        try:
            # OpenCV loads as BGR, convert to RGB for standard PyTorch models
            img_bgr = cv2.imread(str(full_path))
            if img_bgr is None:
                raise FileNotFoundError(f"Image not found or corrupted: {full_path}")
                
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            tensor_img = self.vision_transform(pil_img)
            return tensor_img
        except Exception as e:
            logging.warning(f"Vision loading failed for {full_path}: {e}")
            # Instead of crashing training, we could return a zero-tensor 
            # so the model learns to handle missing frames, 
            # but returning zero tensor directly requires shape knowledge.
            return torch.zeros((3, 224, 224), dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.valid_indices)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        """
        Retrieves a multimodal sample corresponding to a precise temporal window.
        
        Depending on the config flags, it grabs visual frames, physics/IMU 1D streams, 
        and ground truth labels. Outputs are packed into a dictionary for dynamic routing
        in the Fusion Engine.
        
        Expected Tensor Shapes:
            - 'imu': [Sequence_Length, Num_Features] (e.g., [100, 6])
            - 'vision': [Channels, Height, Width] (e.g., [3, 224, 224])
            - 'label': [1] (Scalar Long)
        
        Args:
            idx (int): The relative window index.

        Returns:
            Dict[str, Any]: A dictionary grouping all active modalities and labels.
        """
        start_idx = self.valid_indices[idx]
        end_idx = start_idx + self.seq_len
        
        # Slicing the dataframe for the current window
        window_df = self.data_df.iloc[start_idx:end_idx]
        
        sample: Dict[str, Any] = {}
        
        # 1. Load Physics / 1D Modality
        if self.config.model_settings.use_imu:
            imu_array = window_df[self.feature_cols].values # typical shape: (100, 6)
            # Impute any lingering NaN values with 0.0 before casting to tensor
            imu_array = np.nan_to_num(imu_array, nan=0.0)
            sample['imu'] = torch.tensor(imu_array, dtype=torch.float32) 
            
        # 2. Load Vision Modality (using the frame at the *end* of the IMU sequence)
        if self.config.model_settings.use_vision:
            if self.image_path_col in window_df.columns:
                target_image_path = window_df.iloc[-1][self.image_path_col]
                if pd.notna(target_image_path):
                    sample['vision'] = self.load_image(str(target_image_path))
                else:
                    sample['vision'] = torch.zeros((3, 224, 224), dtype=torch.float32)
            else:
                logging.warning(f"Vision flag is True, but {self.image_path_col} column is missing.")
                sample['vision'] = torch.zeros((3, 224, 224), dtype=torch.float32)

        # 3. Load Target Label (Standard assumes the final step of the window dictates the label)
        raw_label = window_df.iloc[-1][self.label_col]
        
        # CycleSafe: Labels might be string text (e.g., 'pedaling', 'coasting'). 
        # Need a safe fallback to generic int mapping if strings are present.
        if isinstance(raw_label, str):
             # Placeholder map, you'll need the exact string names from Label.csv
             label_map = {'pedaling': 0, 'coasting': 1, 'braking': 2}
             # Default to 0 if unknown to prevent crashes
             raw_label = label_map.get(raw_label.lower().strip(), 0) 
             
        # Treat as classification index
        sample['label'] = torch.tensor(int(raw_label), dtype=torch.long)
        
        return sample

if __name__ == "__main__":
    # Test execution / Validation logic
    logging.info("Dataset module compiled successfully.")
    # Expected instantiation logic:
    # cfg = load_config("../config.yaml")
    # tfms = T.Compose([T.Resize((256, 256)), T.ToTensor()])
    # dataset = MultimodalRoadDataset(
    #     csv_path="../processed_data/aligned_dataset.csv",
    #     config=cfg,
    #     feature_cols=['Acc-X', 'Acc-Y', 'Acc-Z'],
    #     label_col='Label',
    #     vision_transform=tfms
    # )
    # print(dataset[0]['imu'].shape) # Expected: torch.Size([100, 3])
