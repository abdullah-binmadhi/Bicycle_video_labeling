import numpy as np
from scipy import signal
import pandas as pd

class QuarterCarDSP:
    """
    Quarter-Car DSP Filter.
    Removes low-frequency suspension bounce (~<3.0Hz) to isolate high-frequency road textures.
    Upgraded to include GPS Velocity Fusion scaling.
    """
    def __init__(self, cutoff_freq=3.0, fs=50.0, order=4):
        self.cutoff = cutoff_freq
        self.fs = fs
        self.nyq = 0.5 * fs
        self.order = order
        # Highpass butterworth
        self.b, self.a = signal.butter(self.order, self.cutoff/self.nyq, btype='high')

    def apply_filter(self, data):
        """Applies the zero-phase Butterworth filter along the sequence."""
        # Check if data is too short
        if len(data) <= 15:
            return data
            
        # Apply filtfilt (zero phase) on axis 0 (time)
        return signal.filtfilt(self.b, self.a, data, axis=0)

    def apply_velocity_fusion(self, filtered_data, speed_array):
        """
        Normalizes high-frequency vibrations by vehicle speed.
        (vibrations naturally increase at higher speeds).
        Adds a safety clamp to avoid division by zero.
        """
        safe_speed = np.clip(speed_array, 1.0, 50.0) # Clamp speed between 1 m/s and 50 m/s
        return filtered_data / (safe_speed ** 0.5)

    def process_dataframe(self, df):
        """Filters all Acc and Gyr columns in a pandas DataFrame."""
        out_df = df.copy()
        target_cols = [c for c in out_df.columns if 'Acc' in c or 'Gyr' in c]
        
        # Check if GPS Speed is available for advanced fusion
        speed_col = next((c for c in out_df.columns if 'Speed' in c or 'Velocity' in c), None)
        
        for col in target_cols:
            filtered_signal = self.apply_filter(out_df[col].values)
            
            if speed_col is not None:
                filtered_signal = self.apply_velocity_fusion(filtered_signal, out_df[speed_col].values)
                
            out_df[col] = filtered_signal
            
        return out_df
