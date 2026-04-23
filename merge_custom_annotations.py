import pandas as pd
import sys
import numpy as np

def merge_datasets(aligned_csv_path, manual_csv_path, output_csv_path):
    print(f"Loading aligned data from {aligned_csv_path}...")
    try:
        aligned_df = pd.read_csv(aligned_csv_path)
    except FileNotFoundError:
        print(f"Error: {aligned_csv_path} not found.")
        sys.exit(1)

    print(f"Loading manual annotations from {manual_csv_path}...")
    try:
        manual_df = pd.read_csv(manual_csv_path)
    except FileNotFoundError:
        print(f"Error: {manual_csv_path} not found.")
        sys.exit(1)

    if len(manual_df) == 0:
        print("Manual annotations are empty.")
        sys.exit(1)

    # Clean up column names and sort
    aligned_df = aligned_df.sort_values(by="NTP")
    manual_df = manual_df.sort_values(by="timestamp")

    # Assuming the start of the video (timestamp 0.0) matches the first NTP in aligned data
    base_ntp = aligned_df["NTP"].min()
    
    # Calculate equivalent NTP for each manual annotation
    manual_df["NTP"] = base_ntp + (manual_df["timestamp"] * 1000)

    print("Merging annotations into IMU data (snapping to nearest timestamp)...")
    # We use merge_asof to find the closest sensor reading for each annotation
    # But wait, usually we want to label the continuous IMU data!
    # For each row in aligned_df, what is the current label?
    # We can do merge_asof in reverse: snap labels onto aligned_df
    
    # Let's just create a continuous label column
    # For a video, if a label appears at t=2.0s, does it last until t=3.0s?
    # Let's use merge_asof backward so that aligned_df rows get the most recent label.
    # To prevent labels from leaking too far, we can set a tolerance (e.g., 2000 ms = 2 seconds)
    
    merged_df = pd.merge_asof(
        aligned_df,
        manual_df[["NTP", "label", "confidence"]],
        on="NTP",
        direction="backward",
        tolerance=1000 # Labels persist for 1 second max
    )

    # Fill empty labels with 'Unclassified'
    merged_df["class_name"] = merged_df["label"].fillna("Unclassified")
    merged_df.drop(columns=["label"], inplace=True)

    print(f"Saving merged dataset to {output_csv_path}...")
    merged_df.to_csv(output_csv_path, index=False)
    
    print(f"Merge successful! Total rows: {len(merged_df)}")
    print("Label distribution in merged dataset:")
    print(merged_df["class_name"].value_counts())

if __name__ == "__main__":
    ALIGNED_CSV = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/Project Surface Detection/LM-17.06/876ED8BA-AF81-4DCD-9A29-8702D236B21D/csv and checkpoints/aligned_dataset.csv"
    MANUAL_CSV = "manual_annotations.csv"
    OUTPUT_CSV = "/Users/abdullahbinmadhi/Desktop/Bicycle Video ML Model/Project Surface Detection/LM-17.06/876ED8BA-AF81-4DCD-9A29-8702D236B21D/csv and checkpoints/aligned_dataset_labeled.csv"
    
    merge_datasets(ALIGNED_CSV, MANUAL_CSV, OUTPUT_CSV)
