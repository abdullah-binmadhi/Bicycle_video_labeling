import pandas as pd
import numpy as np
from data_pipeline.synchronizer import DataSynchronizer
import os
import argparse

# mock config
class Config:
    pass
config = Config()
class DataPaths:
    pass
config.data_paths = DataPaths()
config.data_paths.sensor_data_dir = "dummy"
config.data_paths.processed_dir = "dummy_out"

# test case
base_df = pd.DataFrame({
    'NTP': [1000.0, 1050.0, 1100.0, 1150.0, 1200.0, 1250.0, 1300.0],
    'Acc-X': [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6],
    'Acc-Y': [0.1]*7,
    'Acc-Z': [9.8]*7
})

# Let's say aux_df has labels at 1000.0 and 1300.0
# The label at 1300.0 is slightly offset
aux_df = pd.DataFrame({
    'NTP': [999.0, 1290.0],
    'Label': ['A', 'B']
})

class MockArgs:
    tolerance = 20
    gap_handling = "ffill"
    apply_dsp = False
    output_dir = "dummy_out"

print("--- Testing ffill with tolerance 20 ---")
sync = DataSynchronizer(config, MockArgs())
merged_df = sync.merge_streams(base_df.copy(), aux_df.copy(), time_col='NTP', tolerance_ms=20, direction='nearest')
print("After merge_streams:")
print(merged_df[['NTP', 'Acc-X', 'Label']])

handled_df = sync.handle_missing_data(merged_df.copy(), continuous_cols=[], discrete_cols=['Label'])
print("After handle_missing_data (ffill):")
print(handled_df[['NTP', 'Acc-X', 'Label']])

print("\n--- Testing drop with tolerance 20 ---")
args2 = MockArgs()
args2.gap_handling = "drop"
sync2 = DataSynchronizer(config, args2)
merged_df2 = sync2.merge_streams(base_df.copy(), aux_df.copy(), time_col='NTP', tolerance_ms=20, direction='nearest')

handled_df2 = sync2.handle_missing_data(merged_df2.copy(), continuous_cols=[], discrete_cols=['Label'])
if 'Label' in handled_df2.columns:
    handled_df2.dropna(subset=['Label'], inplace=True)
print("After handle_missing_data (drop):")
print(handled_df2[['NTP', 'Acc-X', 'Label']])

