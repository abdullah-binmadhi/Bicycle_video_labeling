import pandas as pd
from pathlib import Path
import glob

files = glob.glob("/Users/abdullahbinmadhi/Desktop/**/aligned_dataset.csv", recursive=True)
if files:
    for f in files:
        print(f"File: {f}")
        df = pd.read_csv(f, nrows=2)
        print("Columns:", list(df.columns))
else:
    print("No files found")
