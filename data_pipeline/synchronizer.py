import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional

from config_loader import FrameworkConfig, load_config

# Configure basic logging for the synchronizer
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s', stream=sys.stdout)

class DataSynchronizer:
    """
    Core synchronization engine that aligns multimodal sensor streams.
    
    Given the disparate sampling rates of sensor streams (e.g., IMU @ 100Hz,
    Video/LIDAR @ 10-30Hz), this engine designates the highest-frequency 
    stream (typically Accelerometer/IMU) as the base timeline. It then uses 
    `pandas.merge_asof` to perform temporal alignment using absolute UNIX timestamps.
    """

    def __init__(self, config: FrameworkConfig):
        """
        Initializes the synchronizer with pipeline configuration.

        Args:
            config (FrameworkConfig): System configuration containing paths and rates.
        """
        self.config = config
        self.base_dir = Path(config.data_paths.sensor_data_dir)
        self.processed_dir = Path(config.data_paths.processed_dir)
        
        # Ensure the output directory exists
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def load_stream(self, file_path: Path, time_col: str = "NTP") -> Optional[pd.DataFrame]:
        """
        Loads a single sensor CSV file and prepares its timestamp index.
        Specifically robust for 'CycleSafe' Date/Time strings.
        """
        if not file_path.exists():
            logging.error(f"Sensor file missing: {file_path}")
            return None

        try:
            df = pd.read_csv(file_path)
            if time_col not in df.columns:
                raise ValueError(f"Column '{time_col}' missing in {file_path}")
            
            # Convert string timestamps to normalized datetime objects, then to unix milliseconds
            if df[time_col].dtype == object:
                 df[time_col] = pd.to_datetime(df[time_col], errors='coerce').astype('int64') // 10**6

            # Force all timestamps to float64 to ensure matching datatypes during merge_asof
            df[time_col] = df[time_col].astype('float64')

            df.dropna(subset=[time_col], inplace=True)
            df.sort_values(by=time_col, inplace=True)
            
            # Auto-rename raw X,Y,Z based on file name if needed
            fname = str(file_path).lower()
            if 'accel' in fname:
                df.rename(columns={'X': 'Acc-X', 'Y': 'Acc-Y', 'Z': 'Acc-Z'}, inplace=True)
            elif 'gyro' in fname:
                df.rename(columns={'X': 'Gyr-X', 'Y': 'Gyr-Y', 'Z': 'Gyr-Z'}, inplace=True)
                
            # Drop the common useless columns to prevent _x _y suffix explosion in merge
            columns_to_drop = ['Timestamp', 'Video', 'Unnamed: 0']
            for c in columns_to_drop:
                if c in df.columns:
                    df.drop(columns=[c], inplace=True)
                    
            return df

        except Exception as e:
            logging.error(f"Error loading {file_path}: {e}")
            return None

    def merge_streams(self, 
                      base_df: pd.DataFrame, 
                      aux_df: pd.DataFrame, 
                      time_col: str = "timestamp", 
                      tolerance_ms: int = 50,
                      direction: str = "backward") -> pd.DataFrame:
        """
        Merges an auxiliary sensor dataframe onto the base dataframe using nearest time.

        Uses `pandas.merge_asof` which operates in O(n) assuming sorted indices,
        doing a nearest or backward lookup within a specified tolerance.

        Args:
            base_df (pd.DataFrame): The highest frequency sensor dataframe (e.g., IMU).
            aux_df (pd.DataFrame): Incoming lower-frequency data (e.g., GNSS, LIDAR features).
            time_col (str): Shared timestamp column.
            tolerance_ms (int): Max time drift allowed (in milliseconds) before dropping.
                                Assumes timestamp is in seconds if floating point, adjust accordingly.
            direction (str): 'backward', 'nearest', or 'forward'. 'backward' is standard 
                             causal alignment (we only use past/present auxiliary data).

        Returns:
            pd.DataFrame: Temporally aligned unified dataframe.
        """
        # Note: If `time_col` is represented in seconds, convert tolerance to seconds.
        # Here we assume timestamps are raw milliseconds or we map the tolerance raw value directly.
        # Change `tolerance_ms` appropriately based on the actual units of the user CSV timestamp.
        try:
            merged = pd.merge_asof(
                base_df, 
                aux_df, 
                on=time_col, 
                tolerance=tolerance_ms, 
                direction=direction
            )
            return merged
        except pd.errors.MergeError as e:
            logging.error(f"Merge error occurred: {e}")
            raise

    def handle_missing_data(self, df: pd.DataFrame, continuous_cols: List[str], discrete_cols: List[str]) -> pd.DataFrame:
        """
        Applies specific imputation logic for different types of signals.
        - Linear interpolation for continuous physical signals (IMU).
        - Forward-fill for discrete/low-frequency signals (LIDAR descriptors, Video boxes, GNSS limits).

        Args:
            df (pd.DataFrame): The un-imputed, merged master dataframe.
            continuous_cols (List[str]): Columns requiring linear interpolation.
            discrete_cols (List[str]): Columns requiring forward filling.

        Returns:
            pd.DataFrame: Imputed master dataframe.
        """
        logging.info("Applying missing data imputation strategies...")
        
        # 1. Forward-fill discrete features first limit the propagation to prevent stale data
        for col in discrete_cols:
            if col in df.columns:
                # Limit limit=10 implies that if a signal is dropped for >> 10 frames, it turns NaN
                df[col] = df[col].ffill(limit=self.config.sensor_rates.imu_hz // 2)

        # 2. Linear interpolate continuous sensor gaps
        for col in continuous_cols:
            if col in df.columns:
                df[col] = df[col].interpolate(method='linear', limit=5, limit_direction='both')

        # NOTE: Removed dropna here to prevent wiping out entire dataset if one module 
        # (like an empty label placeholder) fails interpolation.
        return df

    def process_session(self, base_file: Path, auxiliary_files: Dict[str, Path], time_col: str = "NTP", session_id: str = "") -> Optional[pd.DataFrame]:
        """
        Orchestrates the synchronization flow for a single session.
        Uses NTP base times for CycleSafe data alignment.
        """
        logging.info(f"Starting synchronization pipeline for session {session_id}...")
        
        # 1. Load base timeline
        base_df = self.load_stream(base_file, time_col)
        if base_df is None or len(base_df) == 0:
            return None

        # 2. Iteratively align all auxiliary streams
        master_df = base_df.copy()
        for name, aux_path in auxiliary_files.items():
            aux_df = self.load_stream(aux_path, time_col)
            if aux_df is not None and not aux_df.empty:
                # 100ms tolerance is reasonable for 50Hz data matching with minor drift
                master_df = self.merge_streams(master_df, aux_df, time_col, tolerance_ms=100, direction="nearest")
            else:
                logging.warning(f"Skipping {name} due to load failure or empty data in {session_id}.")

        # 3. Handle interpolation 
        # Using exact CycleSafe columns based on paper details
        continuous = ['Acc-X', 'Acc-Y', 'Acc-Z', 'Gyr-X', 'Gyr-Y', 'Gyr-Z']
        discrete   = ['Label']
        master_df = self.handle_missing_data(master_df, continuous_cols=continuous, discrete_cols=discrete)

        if 'Label' in master_df.columns:
            master_df['Label'] = master_df['Label'].fillna('pedaling')

        master_df.dropna(subset=['Acc-X', 'Gyr-X'], inplace=True)
        
        if len(master_df) == 0:
            return None

        # 4. Add session tracker
        master_df['session_id'] = session_id

        return master_df

    def run_pipeline_all_sessions(self, root_dir: Path, time_col: str = "NTP") -> Optional[Path]:
        all_dfs = []

        def process_dir_internal(session_dir: Path):
            session_id = session_dir.name
            # Check for Accel - if not in root, maybe in an 'Accelerometer' folder
            base_imu = session_dir / "Accelerometer.csv"
            if not base_imu.exists():
                base_imu = session_dir / "Accelerometer" / "Accelerometer.0.csv"
            if not base_imu.exists():
                base_imu = session_dir / "accelerometer" / "0.csv"
            if not base_imu.exists():
                return None
            
            aux_sensors = {}
            for sensor, file_names in [
                ("Gyroscope", ["Gyroscope.csv", "Gyroscope/Gyroscope.0.csv", "gyroscope/0.csv"]),
                ("Label", ["Label.csv", "Label/Label.0.csv", "Label.0.csv", "clip/Label.0.csv"])
            ]:
                for fn in file_names:
                    path = session_dir / fn
                    if path.exists():
                        aux_sensors[sensor] = path
                        break
            
            return self.process_session(base_imu, aux_sensors, time_col, session_id=session_id)

        # 1. Check if the chosen root_dir is itself a direct session folder
        if (root_dir / "Accelerometer.csv").exists() or (root_dir / "Accelerometer" / "Accelerometer.0.csv").exists() or (root_dir / "accelerometer" / "0.csv").exists():
            logging.info(f"Direct session folder detected: {root_dir}")
            df = process_dir_internal(root_dir)
            if df is not None:
                all_dfs.append(df)
        else:
            # 2. Iterate over potential sub-structures (direct children or inside iOS/Android)
            for platform in ['Android', 'iOS', 'Training', 'Validation', '']:
                platform_dir = root_dir / platform if platform else root_dir
                if not platform_dir.exists(): continue
                    
                for session_dir in platform_dir.iterdir():
                    if not session_dir.is_dir(): continue
                    # To prevent infinite recursion if '' matched the root dir:
                    if session_dir == root_dir: continue 
                    df = process_dir_internal(session_dir)
                    if df is not None:
                        all_dfs.append(df)
        
        if not all_dfs:
            logging.error("No valid sessions found to consolidate!")
            return None

        # Concatenate everything
        master_df = pd.concat(all_dfs, ignore_index=True)
        output_path = self.processed_dir / "aligned_dataset.csv"
        master_df.to_csv(output_path, index=False)
        logging.info(f"Successfully saved concatenated multimodal dataset with {len(all_dfs)} sessions to {output_path}")
        
        return output_path

if __name__ == "__main__":
    import sys
    import os
    import argparse
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config_loader import load_config
    
    parser = argparse.ArgumentParser(description="Synchronize Modal Data.")
    parser.add_argument("--data_dir", type=str, help="Path to main BicycleData folder", default="")
    args = parser.parse_args()

    # Rapid Verification Test using actual files
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    cfg = load_config(config_path)
    synchronizer = DataSynchronizer(cfg)
    
    # Process all sessions inside given data dir or fallback to BicycleData
    if args.data_dir:
        bicycle_data_dir = Path(args.data_dir)
    else:
        bicycle_data_dir = Path("/Users/abdullahbinmadhi/Desktop/Bicycle ML/Project Surface Detection/BicycleData")
        if not bicycle_data_dir.exists():
            # Fallback to current directory structure if previous isn't found
            bicycle_data_dir = Path("../Project Surface Detection/BicycleData")
            
    if not bicycle_data_dir.exists():
        logging.error(f"Provided data directory not found: {bicycle_data_dir}")
        sys.exit(1)
        
    output = synchronizer.run_pipeline_all_sessions(bicycle_data_dir, time_col="NTP")
    
    if output:
        logging.info("Synchronization complete. Check processed_data/aligned_dataset.csv.")
    else:
        logging.error("Synchronization failed.")
