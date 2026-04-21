import os
import sys
import cv2
import argparse
import datetime
import calendar
import re
import csv
import numpy as np

def parse_filename_time(filename):
    """
    Attempts to extract a timestamp from common filename patterns (e.g. YYYYMMDD_HHMMSS)
    Returns a unix timestamp (float) if found, otherwise None.
    """
    match = re.search(r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', filename)
    if match:
        year, month, day, hour, minute, second = map(int, match.groups())
        try:
            dt = datetime.datetime(year, month, day, hour, minute, second)
            return dt.timestamp()
        except ValueError:
            pass
    return None

def load_imu_data(imu_csv_path):
    if not os.path.exists(imu_csv_path):
        return []
    
    imu_data = []
    with open(imu_csv_path, 'r') as f:
        reader = csv.DictReader(f)
        time_col = next((c for c in reader.fieldnames if 'time' in c.lower()), None)
        speed_col = next((c for c in reader.fieldnames if 'speed' in c.lower() or 'velocity' in c.lower()), None)
        
        if time_col and speed_col:
            for row in reader:
                try:
                    t = float(row[time_col])
                    s = float(row[speed_col])
                    imu_data.append((t, s))
                except (ValueError, TypeError):
                    pass
                    
    imu_data.sort(key=lambda x: x[0])
    return imu_data

def get_speed_at_time(imu_data, timestamp, max_diff=2.0):
    if not imu_data:
        return None
    import bisect
    times = [x[0] for x in imu_data]
    idx = bisect.bisect_left(times, timestamp)
    
    best_idx = idx
    if idx == 0:
        best_idx = 0
    elif idx == len(times):
        best_idx = len(times) - 1
    else:
        before = idx - 1
        after = idx
        if abs(times[after] - timestamp) < abs(times[before] - timestamp):
            best_idx = after
        else:
            best_idx = before
            
    if abs(times[best_idx] - timestamp) <= max_diff:
        return imu_data[best_idx][1]
    return None

def extract_frames(video_path, output_dir, target_fps=10, override_start_time=None, diff_threshold=0.0, imu_csv=None):
    if not os.path.exists(video_path):
        print(f"Error: Video file {video_path} not found.")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    
    start_timestamp = 0.0
    if override_start_time:
        try:
            start_timestamp = float(override_start_time)
            print(f"Using provided start timestamp: {start_timestamp}")
        except ValueError:
            try:
                dt = datetime.datetime.fromisoformat(override_start_time)
                start_timestamp = dt.timestamp()
                print(f"Parsed provided start time: {start_timestamp}")
            except Exception as e:
                print(f"Could not parse override_start_time: {override_start_time}. Defaulting to 0.")
    else:
        filename = os.path.basename(video_path)
        parsed_time = parse_filename_time(filename)
        if parsed_time:
            start_timestamp = float(parsed_time)
            print(f"Extracted start timestamp from filename: {start_timestamp}")
        else:
            print("No timestamp in filename and no override provided. Defaulting to 0.")
            
    print(f"Extracting frames from {video_path} at ~{target_fps} FPS to {output_dir}")
    print(f"Base Unix Timestamp: {start_timestamp}")
    
    imu_data = []
    if imu_csv:
        print(f"Loading IMU/GNSS data from {imu_csv}...")
        imu_data = load_imu_data(imu_csv)
        print(f"Loaded {len(imu_data)} IMU records.")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        sys.exit(1)

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps <= 0:
        video_fps = 30.0 # Fallback
        
    total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
    frame_interval = int(round(video_fps / float(target_fps)))
    if frame_interval < 1:
        frame_interval = 1
        
    expected_saves = total_video_frames // frame_interval if total_video_frames > 0 else "Unknown"

    frame_count = 0
    saved_count = 0
    skipped_ssim = 0
    skipped_imu = 0
    
    last_saved_frame_gray = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            current_time_offset = frame_count / video_fps
            current_timestamp = start_timestamp + current_time_offset
            
            save_this_frame = True
            
            if imu_data:
                speed = get_speed_at_time(imu_data, current_timestamp)
                if speed is not None and speed < 0.5:
                    if frame_count % (frame_interval * 5) != 0:
                        save_this_frame = False
                        skipped_imu += 1
            
            if save_this_frame and diff_threshold > 0.0:
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                small_curr = cv2.resize(gray_frame, (128, 128))
                
                if last_saved_frame_gray is not None:
                    diff = cv2.absdiff(small_curr, last_saved_frame_gray)
                    mean_diff = np.mean(diff) / 255.0
                    
                    if mean_diff < diff_threshold:
                        save_this_frame = False
                        skipped_ssim += 1
                
                if save_this_frame:
                    last_saved_frame_gray = small_curr
            
            if save_this_frame:
                out_name = f"frame_{current_timestamp:.3f}.jpg"
                out_path = os.path.join(output_dir, out_name)
                cv2.imwrite(out_path, frame)
                saved_count += 1
            
            if (saved_count + skipped_ssim + skipped_imu) % 100 == 0:
                print(f"Processed {(saved_count + skipped_ssim + skipped_imu)}/{expected_saves} target frames... (Saved: {saved_count}, Skipped SSIM: {skipped_ssim}, Skipped IMU: {skipped_imu})")

        frame_count += 1

    cap.release()
    print(f"Extraction complete! Saved {saved_count} frames to {output_dir}")
    if diff_threshold > 0.0 or imu_data:
        print(f"Smart Extraction Result: Dropped {skipped_ssim} identical frames, {skipped_imu} stationary frames.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract frames from a video based on timestamps.")
    parser.add_argument("--video", type=str, required=True, help="Path to input video file")
    parser.add_argument("--out_dir", type=str, required=True, help="Directory to save extracted frames")
    parser.add_argument("--fps", type=float, default=10.0, help="Target extraction FPS")
    parser.add_argument("--start_time", type=str, default=None, help="UNIX timestamp or ISO date string (Overrides filename parsing)")
    parser.add_argument("--diff_threshold", type=float, default=0.0, help="Similarity threshold to skip identical frames (0.0 to disable)")
    parser.add_argument("--imu_csv", type=str, default=None, help="Path to IMU/GNSS CSV to drop stationary frames")
    
    args = parser.parse_args()
    
    extract_frames(args.video, args.out_dir, args.fps, args.start_time, args.diff_threshold, args.imu_csv)
