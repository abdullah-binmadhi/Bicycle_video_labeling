import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import argparse

from config_loader import load_config, FrameworkConfig

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s', stream=sys.stdout)

class DataSynchronizer:
    def __init__(self, config: FrameworkConfig, args=None):
        self.config = config
        self.base_dir = Path(config.data_paths.sensor_data_dir)
        self.processed_dir = Path(config.data_paths.processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        self.tolerance_ms = int(getattr(args, "tolerance", 50)) if args else 50
        self.gap_handling = getattr(args, "gap_handling", "ffill") if args else "ffill"
        self.apply_dsp = getattr(args, "apply_dsp", False) if args else False
        
        self.stats = {
            "total_rows": 0,
            "dropped_rows": 0,
            "classes": {}
        }

    def load_stream(self, file_path: Path, time_col: str = "NTP") -> Optional[pd.DataFrame]:
        if not file_path.exists():
            return None
        try:
            df = pd.read_csv(file_path)
            if time_col not in df.columns:
                return None
            if df[time_col].dtype == object:
                 df[time_col] = pd.to_datetime(df[time_col], errors='coerce').astype('int64') // 10**6
            df[time_col] = df[time_col].astype('float64')
            df.dropna(subset=[time_col], inplace=True)
            df.sort_values(by=time_col, inplace=True)
            
            fname = str(file_path).lower()
            if 'accel' in fname or 'imu' in fname:
                df.rename(columns={'X': 'Acc-X', 'Y': 'Acc-Y', 'Z': 'Acc-Z'}, inplace=True)
            elif 'gyro' in fname:
                df.rename(columns={'X': 'Gyr-X', 'Y': 'Gyr-Y', 'Z': 'Gyr-Z'}, inplace=True)
                
            for c in ['Timestamp', 'Video', 'Unnamed: 0']:
                if c in df.columns: df.drop(columns=[c], inplace=True)
            return df
        except Exception as e:
            return None

    def merge_streams(self, base_df: pd.DataFrame, aux_df: pd.DataFrame, time_col: str = "NTP", tolerance_ms: int = 50, direction: str = "backward") -> pd.DataFrame:
        try:
            return pd.merge_asof(base_df, aux_df, on=time_col, tolerance=tolerance_ms, direction=direction)
        except pd.errors.MergeError as e:
            return base_df

    def handle_missing_data(self, df: pd.DataFrame, continuous_cols: List[str], discrete_cols: List[str]) -> pd.DataFrame:
        if self.gap_handling == 'ffill':
            for col in discrete_cols:
                if col in df.columns: df[col] = df[col].ffill(limit=50)
            for col in continuous_cols:
                if col in df.columns: df[col] = df[col].interpolate(method='linear', limit=5, limit_direction='both')
        elif self.gap_handling == 'interpolate':
            # interpolate discrete? Fallback to ffill for discrete, but heavily interpolate continuous
            for col in discrete_cols:
                if col in df.columns: df[col] = df[col].ffill(limit=500)
            for col in continuous_cols:
                if col in df.columns: df[col] = df[col].interpolate(method='linear', limit=200, limit_direction='both')
        elif self.gap_handling == 'drop':
            pass # We will drop nans outside
        return df

    def process_session(self, base_file: Path, auxiliary_files: Dict[str, Path], time_col: str = "NTP", session_id: str = "") -> Optional[pd.DataFrame]:
        base_df = self.load_stream(base_file, time_col)
        if base_df is None or len(base_df) == 0:
            return None

        import copy
        master_df = base_df.copy()
        original_size = len(master_df)
        
        for name, aux_path in auxiliary_files.items():
            aux_df = self.load_stream(aux_path, time_col)
            if aux_df is not None and not aux_df.empty:
                master_df = self.merge_streams(master_df, aux_df, time_col, tolerance_ms=self.tolerance_ms, direction="nearest")

        continuous = ['Acc-X', 'Acc-Y', 'Acc-Z', 'Gyr-X', 'Gyr-Y', 'Gyr-Z']
        discrete   = ['Label']
        master_df = self.handle_missing_data(master_df, continuous_cols=continuous, discrete_cols=discrete)

        if 'Label' in master_df.columns:
            if self.gap_handling == 'drop':
                master_df.dropna(subset=['Label'], inplace=True)
            else:
                master_df['Label'] = master_df['Label'].fillna('unlabeled')

        master_df.dropna(subset=['Acc-X'], inplace=True)
        
        if len(master_df) == 0:
            return None

        # Apply basic DSP if requested
        if self.apply_dsp:
            from scipy.signal import butter, lfilter
            def butter_lowpass_filter(data, cutoff, fs, order=5):
                nyq = 0.5 * fs
                normal_cutoff = cutoff / nyq
                b, a = butter(order, normal_cutoff, btype='low', analog=False)
                return lfilter(b, a, data)
                
            for c in ['Acc-Z']:
                if c in master_df.columns:
                    master_df[c] = butter_lowpass_filter(master_df[c].values, cutoff=5, fs=50)

        master_df['session_id'] = session_id
        
        self.stats["total_rows"] += len(master_df)
        self.stats["dropped_rows"] += (original_size - len(master_df))
        
        if 'Label' in master_df.columns:
            for cls, count in master_df['Label'].value_counts().items():
                self.stats["classes"][cls] = self.stats["classes"].get(cls, 0) + int(count)

        return master_df

    def run_pipeline_all_sessions(self, root_dir: Path, time_col: str = "NTP") -> Optional[Path]:
        all_dfs = []

        def process_dir_internal(session_dir: Path):
            session_id = session_dir.name
            base_imu = session_dir / "Accelerometer.csv"
            if not base_imu.exists(): base_imu = session_dir / "Accelerometer" / "Accelerometer.0.csv"
            if not base_imu.exists(): base_imu = session_dir / "accelerometer" / "0.csv"
            if not base_imu.exists(): return None
            
            aux_sensors = {}
            for sensor, file_names in [
                ("Gyroscope", ["Gyroscope.csv", "Gyroscope/Gyroscope.0.csv", "gyroscope/0.csv"]),
                ("Label", ["Label.csv", "Label/Label.0.csv", "Label.0.csv", "clip/Label.0.csv", "csv and checkpoints/Label.0.csv"])
            ]:
                for fn in file_names:
                    path = session_dir / fn
                    if path.exists():
                        aux_sensors[sensor] = path
                        break
            
            return self.process_session(base_imu, aux_sensors, time_col, session_id=session_id)

        if (root_dir / "Accelerometer.csv").exists() or (root_dir / "Accelerometer" / "Accelerometer.0.csv").exists() or (root_dir / "accelerometer" / "0.csv").exists():
            df = process_dir_internal(root_dir)
            if df is not None: 
                all_dfs.append(df)
            else:
                logging.error(f"Failed to process the root session directory: {root_dir}")
        else:
            # Check for sub-folders (Legacy search)
            for platform in ['Android', 'iOS', 'Training', 'Validation', '']:
                platform_dir = root_dir / platform if platform else root_dir
                if not platform_dir.exists(): continue
                for session_dir in platform_dir.iterdir():
                    if not session_dir.is_dir() or session_dir == root_dir: continue 
                    df = process_dir_internal(session_dir)
                    if df is not None: all_dfs.append(df)
        
        if not all_dfs:
            logging.error("No valid sessions found to consolidate!")
            return None

        master_df = pd.concat(all_dfs, ignore_index=True)
        output_path = self.processed_dir / "aligned_dataset.csv"
        master_df.to_csv(output_path, index=False)
        print(f"SYNC_STATS:{json.dumps(self.stats)}")
        return output_path
        
    def run_adhoc_session(self, imu_path: Path, label_path: Path, time_col: str = "NTP") -> Optional[Path]:
        aux = {"Label": label_path}
        df = self.process_session(imu_path, aux, time_col, session_id="AdHoc")
        if df is None:
            logging.error("AdHoc merge failed or returned empty.")
            return None
        output_path = self.processed_dir / "adhoc_aligned_dataset.csv"
        df.to_csv(output_path, index=False)
        print(f"SYNC_STATS:{json.dumps(self.stats)}")
        return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synchronize Modal Data.")
    parser.add_argument("--data_dir", type=str, help="Path to main BicycleData folder", default="")
    parser.add_argument("--adhoc", action="store_true", help="Run in ad-hoc solitary file mode")
    parser.add_argument("--imu_csv", type=str, help="Path to AdHoc IMU CSV", default="")
    parser.add_argument("--label_csv", type=str, help="Path to AdHoc Label CSV", default="")
    parser.add_argument("--tolerance", type=int, help="Merge tolerance in ms", default=50)
    parser.add_argument("--gap_handling", type=str, choices=["ffill", "interpolate", "drop"], default="ffill")
    parser.add_argument("--apply_dsp", action="store_true", help="Apply quarter-car DSP filtering")
    args = parser.parse_args()

    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    cfg = load_config(config_path)
    synchronizer = DataSynchronizer(cfg, args)
    
    if args.adhoc:
        if not args.imu_csv or not args.label_csv:
            logging.error("Missing --imu_csv or --label_csv for adhoc mode.")
            sys.exit(1)
        output = synchronizer.run_adhoc_session(Path(args.imu_csv), Path(args.label_csv))
    else:
        bicycle_data_dir = Path(args.data_dir) if args.data_dir else Path("/Users/abdullahbinmadhi/Desktop/Bicycle ML/Project Surface Detection/BicycleData")
        if not bicycle_data_dir.exists():
            bicycle_data_dir = Path("../Project Surface Detection/BicycleData")
            
        if not bicycle_data_dir.exists():
            logging.error(f"Provided data directory not found: {bicycle_data_dir}")
            sys.exit(1)
            
        output = synchronizer.run_pipeline_all_sessions(bicycle_data_dir, time_col="NTP")
    
    if output:
        logging.info(f"Synchronization complete. Output saved to {output}.")
    else:
        logging.error("Synchronization failed.")
