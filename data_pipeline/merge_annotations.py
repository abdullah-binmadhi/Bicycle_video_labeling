import pandas as pd
import sys
import argparse
import os

def parse_args():
    parser = argparse.ArgumentParser(description="Merge manual annotations with aligned IMU telemetry.")
    parser.add_argument("--aligned", required=True, help="Path to aligned_dataset.csv (telemetry)")
    parser.add_argument("--annotations", required=True, help="Path to manual_annotations.csv or master_annotations.csv")
    parser.add_argument("--output", required=True, help="Path to save the merged output CSV")
    return parser.parse_args()

def merge_datasets(aligned_csv_path, manual_csv_path, output_csv_path):
    print(f"Loading aligned data from {aligned_csv_path}...")
    if not os.path.exists(aligned_csv_path):
        print(f"Error: {aligned_csv_path} not found.")
        sys.exit(1)
    aligned_df = pd.read_csv(aligned_csv_path)

    print(f"Loading annotations from {manual_csv_path}...")
    if not os.path.exists(manual_csv_path):
        print(f"Error: {manual_csv_path} not found.")
        sys.exit(1)
    manual_df = pd.read_csv(manual_csv_path)

    if len(manual_df) == 0:
        print("Annotations file is empty.")
        sys.exit(1)

    # Detect if we have 'timestamp' (manual_annotations.csv) or 'image_id' (master_annotations.csv)
    base_ntp = aligned_df["NTP"].min()
    if 'timestamp' in manual_df.columns:
        manual_df = manual_df.sort_values(by="timestamp")
        manual_df["NTP"] = base_ntp + (manual_df["timestamp"].astype(float) * 1000)
    elif 'image_id' in manual_df.columns:
        # e.g., '.../1718593562.413.jpg'
        manual_df['extracted_ts'] = manual_df['image_id'].apply(lambda x: float(os.path.basename(x).replace('.jpg', '')))
        manual_df = manual_df.sort_values(by="extracted_ts")
        # Assuming extracted_ts is Unix epoch in seconds
        manual_df["NTP"] = manual_df["extracted_ts"] * 1000

        # Auto-detect timezone shift (e.g. video recorded in PST vs IMU in UTC)
        aux_start = manual_df["NTP"].min()
        diff_ms = base_ntp - aux_start
        if abs(diff_ms) >= 3600000: # 1 hour
            hours_diff = round(diff_ms / 3600000)
            print(f"Auto-detecting timezone offset of {hours_diff} hours. Adjusting annotations...")
            manual_df["NTP"] += (hours_diff * 3600000)

    else:
        print("Error: Could not find 'timestamp' or 'image_id' column in annotations CSV.")
        sys.exit(1)

    aligned_df = aligned_df.sort_values(by="NTP")

    # Determine label column
    label_col = 'label' if 'label' in manual_df.columns else ('class_name' if 'class_name' in manual_df.columns else None)
    if not label_col:
        print("Error: Could not find 'label' or 'class_name' column in annotations CSV.")
        sys.exit(1)
        
    print("Merging annotations into IMU data (snapping to nearest timestamp)...")
    merged_df = pd.merge_asof(
        aligned_df,
        manual_df[["NTP", label_col]],
        on="NTP",
        direction="backward",
        tolerance=1000 # Labels persist for 1 second max
    )

    merged_df["class_name"] = merged_df[label_col].fillna("Unclassified")
    if label_col != "class_name":
        merged_df.drop(columns=[label_col], inplace=True)

    print(f"Saving merged dataset to {output_csv_path}...")
    merged_df.to_csv(output_csv_path, index=False)
    
    print(f"Merge successful! Total rows: {len(merged_df)}")
    print("Label distribution in merged dataset:")
    print(merged_df["class_name"].value_counts())

if __name__ == "__main__":
    args = parse_args()
    merge_datasets(args.aligned, args.annotations, args.output)
