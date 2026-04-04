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
            # Special handling for frames Label CSV which might have extra spaces/formatting
            if "Label.0.csv" in str(file_path):
                import io
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # The label CSV from Roboflow or some scripts exported \n as literal string characters
                if r'\n' in content:
                    content = content.replace(r'\n', '\n')
                
                df = pd.read_csv(io.StringIO(content))
                
                # If there's no 'frame' column, it implies the file had no header
                if 'frame' not in df.columns:
                    df = pd.read_csv(io.StringIO(content), header=None, names=["frame", "Label", "Conf", "X1", "Y1", "X2", "Y2"])
                
                # Standardize capitalization of the label column
                if 'label' in df.columns and 'Label' not in df.columns:
                    df.rename(columns={'label': 'Label'}, inplace=True)
                
                # Extract timestamp from frame name: frame_1718594185.997.jpg
                def extract_timestamp(s):
                    try:
                        # Find the part between 'frame_' and '.jpg'
                        parts = str(s).split('frame_')
                        if len(parts) > 1:
                            ts_str = parts[1].split('.jpg')[0]
                            return float(ts_str) * 1000.0 # Convert to ms
                    except:
                        pass
                    return None
                df[time_col] = df["frame"].apply(extract_timestamp)
                df.dropna(subset=[time_col], inplace=True)
            else:
                df = pd.read_csv(file_path)
                if time_col not in df.columns:
                    return None
                if str(df[time_col].dtype) in ['object', 'str', 'string']:
                    # Clean up quoted strings like "2024-06-17, 10:51:27.2810"
                    df[time_col] = df[time_col].astype(str).str.replace('"', '').str.strip()
                    # Use specialized format to match "2024-06-17, 10:51:27.2810"
                    df[time_col] = pd.to_datetime(df[time_col], format='%Y-%m-%d, %H:%M:%S.%f', errors='coerce').astype('datetime64[ms]').astype('int64')
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
            logging.error(f"Failed to load {file_path}: {e}", exc_info=True)
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
            try:
                from scipy.signal import butter, lfilter # type: ignore
                def butter_lowpass_filter(data, cutoff, fs, order=5):
                    nyq = 0.5 * fs
                    normal_cutoff = cutoff / nyq
                    b, a = butter(order, normal_cutoff, btype='low', analog=False)
                    return lfilter(b, a, data)
                    
                for c in ['Acc-Z']:
                    if c in master_df.columns:
                        master_df[c] = butter_lowpass_filter(master_df[c].values, cutoff=5, fs=50)
            except ImportError:
                logging.error("The 'scipy' library is required for DSP filtering but is not installed. Please run 'pip install scipy'.")

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
            
            # 1. Base IMU check
            base_imu = None
            for cand in [
                session_dir / "Accelerometer.csv",
                session_dir / "Accelerometer" / "Accelerometer.0.csv",
                session_dir / "accelerometer" / "0.csv"
            ]:
                if cand.exists():
                    base_imu = cand
                    break
            
            if not base_imu: return None
            
            # 2. Aux sensors check
            aux_sensors = {}
            for sensor, file_names in [
                ("Gyroscope", ["Gyroscope.csv", "Gyroscope/Gyroscope.0.csv", "gyroscope/0.csv", "Gyroscope/0.csv"]),
                ("Label", ["Label.csv", "Label/Label.0.csv", "Label.0.csv", "clip/Label.0.csv", "csv and checkpoints/Label.0.csv", "Label/0.csv"])
            ]:
                for fn in file_names:
                    path = session_dir / fn
                    if path.exists():
                        aux_sensors[sensor] = path
                        break
            
            logging.info(f"Processing session: {session_id} in {session_dir}")
            return self.process_session(base_imu, aux_sensors, time_col, session_id=session_id)

        # Main recursion
        logging.info(f"Scanning {root_dir} recursively for session folders...")
        
        # We manually walk to find any folder containing an accelerometer file
        for dirpath, dirnames, filenames in os.walk(root_dir):
            current_dir = Path(dirpath)
            
            # Check if this folder or its immediate children look like a session root
            is_session = (current_dir / "Accelerometer.csv").exists() or \
                         (current_dir / "Accelerometer" / "Accelerometer.0.csv").exists() or \
                         (current_dir / "accelerometer" / "0.csv").exists()
            
            if is_session:
                # To prevent double-processing nested structures, we check if this is a primary session dir
                df = process_dir_internal(current_dir)
                if df is not None:
                    all_dfs.append(df)
                    # Once a session is found, we don't necessarily want to skip children 
                    # (in case of nested sessions), but usually sessions are siblings.
        
        if not all_dfs:
            logging.error(f"No valid sessions found in {root_dir}!")
            return None

        master_df = pd.concat(all_dfs, ignore_index=True)
        output_path = self.processed_dir / "aligned_dataset.csv"
        master_df.to_csv(output_path, index=False)
        print(f"SYNC_STATS:{json.dumps(self.stats)}")
        return output_path
        
    def run_adhoc_session(self, imu_path: Path, label_path: Path, frames_dir: Optional[Path] = None, time_col: str = "NTP") -> Optional[Path]:
        aux = {"Label": label_path}
        # If frames_dir is provided, we might want to check for other sensors there
        # but for AdHoc we usually just merge the two provided files.
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
    parser.add_argument("--frames_dir", type=str, help="Path to Frames Folder", default="")
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
        output = synchronizer.run_adhoc_session(Path(args.imu_csv), Path(args.label_csv), 
                                              frames_dir=Path(args.frames_dir) if args.frames_dir else None)
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
