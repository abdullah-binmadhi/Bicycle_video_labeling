import pandas as pd
import sys
import argparse
import os

def parse_args():
    parser = argparse.ArgumentParser(description="Merge manual annotations with aligned IMU telemetry.")
    parser.add_argument("--aligned", required=True, help="Path to aligned_dataset.csv (telemetry)")
    parser.add_argument("--annotations", required=True, help="Path to master_annotations.csv")
    parser.add_argument("--output", required=True, help="Path to save the merged output CSV")
    return parser.parse_args()

# Surface hazards take priority over objects and signs when multiple
# annotations exist on the same frame.
SURFACE_PRIORITY = [
    'pothole_cluster', 'potholes', 'rail_tracks', 'crack', 'uneven_surface',
    'metal_grating', 'water_puddle', 'drain',
    'cobblestone', 'brick_paving', 'rough_asphalt', 'smooth_asphalt', 'asphalt',
    'manhole', 'crosswalk', 'road_marking',
    'bicycle_lane',
    'pedestrian', 'bicycle', 'car', 'e-scooter',
    'bus_stop', 'stop_sign', 'yield_sign', 'speed_limit_sign',
]
_PRIORITY_MAP = {cls: i for i, cls in enumerate(SURFACE_PRIORITY)}


def _pick_best_label(labels):
    """Return the highest-priority surface class from a list of labels."""
    return min(labels, key=lambda c: _PRIORITY_MAP.get(c.strip(), 999))


def _deduplicate_annotations(manual_df, label_col):
    """
    Collapse multiple annotation rows for the same NTP timestamp into one row,
    selecting the highest-priority surface/hazard class.

    merge_asof requires the right DataFrame to have unique merge-key values.
    Without this step, duplicate NTPs silently corrupt the merge output.
    """
    def _pick(group):
        return _pick_best_label(group[label_col].dropna().tolist() or ['Unclassified'])

    deduped = (
        manual_df.groupby('NTP', sort=True)
        .apply(_pick)
        .reset_index()
    )
    deduped.columns = ['NTP', label_col]
    return deduped.sort_values('NTP').reset_index(drop=True)


def merge_datasets(aligned_csv_path, manual_csv_path, output_csv_path):
    print(f"Loading aligned telemetry from: {aligned_csv_path}")
    if not os.path.exists(aligned_csv_path):
        print(f"Error: {aligned_csv_path} not found.")
        sys.exit(1)
    aligned_df = pd.read_csv(aligned_csv_path, low_memory=False)

    print(f"Loading annotations from: {manual_csv_path}")
    if not os.path.exists(manual_csv_path):
        print(f"Error: {manual_csv_path} not found.")
        sys.exit(1)
    manual_df = pd.read_csv(manual_csv_path)

    if len(manual_df) == 0:
        print("Annotations file is empty.")
        sys.exit(1)

    # ── Step 1: Build NTP column on the annotations ──────────────────────────
    base_ntp = aligned_df["NTP"].min()  # reference point (ms)

    if 'image_id' in manual_df.columns:
        # Filename encodes Unix epoch in seconds: e.g. "1718593562.413.jpg"
        manual_df['_ts_sec'] = manual_df['image_id'].apply(
            lambda x: float(
                os.path.basename(str(x)).replace('.jpg', '').replace('.png', '')
            )
        )
        manual_df['NTP'] = manual_df['_ts_sec'] * 1000.0  # convert to ms

        # ── Step 2: Exact timezone correction ────────────────────────────────
        # Use the precise millisecond diff (not rounded to whole hours) to avoid
        # the ~4.5-second residual gap that the old round(hours) approach left.
        anno_min_ms = manual_df['NTP'].min()
        diff_ms = base_ntp - anno_min_ms

        if abs(diff_ms) >= 3600000:  # at least 1 hour apart → timezone shift
            # Compute exact offset (ms), rounded to nearest second for stability
            exact_offset_ms = round(diff_ms / 1000) * 1000
            hours_approx = exact_offset_ms / 3600000
            print(f"Timezone offset detected: {hours_approx:.3f} h ({exact_offset_ms} ms). Correcting...")
            manual_df['NTP'] += exact_offset_ms

        manual_df = manual_df.drop(columns=['_ts_sec'], errors='ignore')

    elif 'timestamp' in manual_df.columns:
        # Relative seconds since recording start
        manual_df['NTP'] = base_ntp + (manual_df['timestamp'].astype(float) * 1000)

    else:
        print("Error: annotations CSV must have an 'image_id' or 'timestamp' column.")
        sys.exit(1)

    # ── Step 3: Determine label column ───────────────────────────────────────
    label_col = (
        'label' if 'label' in manual_df.columns
        else ('class_name' if 'class_name' in manual_df.columns
              else None)
    )
    if not label_col:
        print("Error: annotations CSV must have a 'label' or 'class_name' column.")
        sys.exit(1)

    print(f"Annotation label column: '{label_col}'")
    print(f"Unique annotated frames (before dedup): {manual_df['NTP'].nunique()}")

    # ── Step 4: Deduplicate — one label per NTP timestamp ────────────────────
    # This is the critical fix. merge_asof silently fails when the right
    # DataFrame has duplicate keys; it produces near-zero matches.
    manual_deduped = _deduplicate_annotations(manual_df, label_col)
    print(f"After deduplication: {len(manual_deduped)} unique annotation timestamps")

    label_counts = manual_deduped[label_col].value_counts()
    print("Label distribution (annotated frames):")
    for cls, cnt in label_counts.items():
        print(f"  {cls}: {cnt} frames")

    # ── Step 5: Merge annotations onto IMU rows ───────────────────────────────
    # Drop any pre-existing class_name column in aligned_df to avoid
    # pandas adding _x / _y suffix confusion.
    aligned_df = aligned_df.drop(columns=['class_name', 'confidence'], errors='ignore')
    aligned_df = aligned_df.sort_values('NTP').reset_index(drop=True)

    print("\nMerging: snapping each annotation to nearest preceding IMU row...")
    merged_df = pd.merge_asof(
        aligned_df,
        manual_deduped[['NTP', label_col]],
        on='NTP',
        direction='backward',
        tolerance=None,  # No fixed tolerance — use forward-fill in next step
    )

    # ── Step 6: Forward-fill labels between annotated frames ─────────────────
    # After merge_asof (backward), IMU rows between two annotation timestamps
    # inherit the label of the most recent annotation. Rows BEFORE the first
    # annotation have NaN. We cap forward-fill at 10 seconds (500 rows at 50Hz)
    # to avoid a label leaking across a very long unlabeled gap.
    MAX_FILL_ROWS = 500  # 10 seconds at 50 Hz

    merged_df['class_name'] = (
        merged_df[label_col]
        .ffill(limit=MAX_FILL_ROWS)
        .fillna('Unclassified')
    )

    # Clean up the intermediate label column if it differs from class_name
    if label_col != 'class_name':
        merged_df.drop(columns=[label_col], inplace=True, errors='ignore')

    # ── Step 7: Save ─────────────────────────────────────────────────────────
    merged_df.to_csv(output_csv_path, index=False)

    print(f"\nSaved merged dataset → {output_csv_path}")
    print(f"Total rows: {len(merged_df)}")
    print("\nFinal class_name distribution:")
    print(merged_df['class_name'].value_counts().to_string())


if __name__ == "__main__":
    args = parse_args()
    merge_datasets(args.aligned, args.annotations, args.output)
