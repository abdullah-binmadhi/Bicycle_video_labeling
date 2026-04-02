import os
import sys
import cv2
import argparse
import datetime
import calendar
import re

def parse_filename_time(filename):
    """
    Attempts to extract a timestamp from common filename patterns (e.g. YYYYMMDD_HHMMSS)
    Returns a unix timestamp (float) if found, otherwise None.
    """
    # Look for a pattern like 20240326_153025
    match = re.search(r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', filename)
    if match:
        year, month, day, hour, minute, second = map(int, match.groups())
        try:
            dt = datetime.datetime(year, month, day, hour, minute, second)
            return dt.timestamp()
        except ValueError:
            pass
    return None

def extract_frames(video_path, output_dir, target_fps=10, override_start_time=None):
    if not os.path.exists(video_path):
        print(f"Error: Video file {video_path} not found.")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    
    # Determine the starting timestamp
    start_timestamp = 0.0
    if override_start_time:
        try:
            start_timestamp = float(override_start_time)
            print(f"Using provided start timestamp: {start_timestamp}")
        except ValueError:
            # Fallback to parsing as datetime string if it's not a float
            try:
                # Assuming format like "YYYY-MM-DD HH:MM:SS" or similar
                dt = datetime.datetime.fromisoformat(override_start_time)
                start_timestamp = dt.timestamp()
                print(f"Parsed provided start time: {start_timestamp}")
            except Exception as e:
                print(f"Could not parse override_start_time: {override_start_time}. Defaulting to 0.")
    else:
        # Option A: Try to parse from filename
        filename = os.path.basename(video_path)
        parsed_time = parse_filename_time(filename)
        if parsed_time:
            start_timestamp = float(parsed_time)
            print(f"Extracted start timestamp from filename: {start_timestamp}")
        else:
            print("No timestamp in filename and no override provided. Defaulting to 0.")
            
    print(f"Extracting frames from {video_path} at ~{target_fps} FPS to {output_dir}")
    print(f"Base Unix Timestamp: {start_timestamp}")

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

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            # Calculate current frame timestamp
            current_time_offset = frame_count / video_fps
            current_timestamp = start_timestamp + current_time_offset
            
            # Save frame
            out_name = f"frame_{current_timestamp:.3f}.jpg"
            out_path = os.path.join(output_dir, out_name)
            cv2.imwrite(out_path, frame)
            saved_count += 1
            
            if saved_count % 100 == 0 or saved_count == expected_saves:
                print(f"Extracted {saved_count}/{expected_saves} frames...")

        frame_count += 1

    cap.release()
    print(f"Extraction complete! Saved {saved_count} frames to {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract frames from a video based on timestamps.")
    parser.add_argument("--video", type=str, required=True, help="Path to input video file")
    parser.add_argument("--out_dir", type=str, required=True, help="Directory to save extracted frames")
    parser.add_argument("--fps", type=float, default=10.0, help="Target extraction FPS")
    parser.add_argument("--start_time", type=str, default=None, help="UNIX timestamp or ISO date string (Overrides filename parsing)")
    
    args = parser.parse_args()
    
    extract_frames(args.video, args.out_dir, args.fps, args.start_time)
