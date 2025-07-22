import os
import argparse
import numpy as np
from tqdm import tqdm
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

from . import logger
from .capture import Capture, Session
from scantools.utils.utils import (
    read_csv, 
    write_csv
)

def nano_to_micro_attr(attr_path: Path):

    attr_name = attr_path.stem
    rows, headers = read_csv(attr_path)

    if not rows or not headers:
        logger.warning(f"No data found for {attr_name} on session {attr_path.parent.name}, skipping.")
        return
    
    if len(rows[0][0]) < 19:
        logger.warning(f"Timestamp are already in milliseconds, skipping {attr_name} on {attr_path.parent.name}.")
        return

    modified_rows = []

    for row in tqdm(rows, desc=logger.info(f"Transforming timestamps for {attr_name} on session {attr_path.parent.name} ...")):

        ts = np.int64(row[0])
        sensor_id = row[1]
        old_image_path = row[2]

        new_ts = np.int64(ts // 1000)

        if attr_name in ('images', 'depths'):

            new_image_path = f"{sensor_id}/{new_ts}-{sensor_id}.png"
            old_image_abs_path = attr_path.parent / 'raw_data' / old_image_path
            new_image_abs_path = attr_path.parent / 'raw_data' / new_image_path
            
            if not old_image_abs_path.exists():
                logger.warning(f"File {old_image_abs_path} does not exist while working on {ts}, skipping.")
                continue
            
            row[2] = new_image_path
            old_image_abs_path.rename(new_image_abs_path)
            
        row[0] = str(new_ts)
        modified_rows.append(row)

    logger.info(f"Processed {len(modified_rows)} for {attr_name} on session {attr_path.parent.name}.")

    write_csv(attr_path, modified_rows, headers)

def get_offset_timestamp(attr_path: Path):
    rows, headers = read_csv(attr_path)
    timestamps = [int(row[0]) for row in rows]  
    if not timestamps: 
        offset = 0
        timestamp_ns = 0
    else:
        timestamp_ns = np.int64(min(timestamps)) 
        timestamp_sec = timestamp_ns / 1e9
        dt = datetime.fromtimestamp(timestamp_sec, tz=timezone.utc)
        minute_start = dt.replace(second=0, microsecond=0)
        minute_start_ns = np.int64(minute_start.timestamp() * 1e9)
        offset = minute_start_ns

    logger.info(f"Timestamp offsets are {timestamp_ns} for {attr_path.stem} on session {attr_path.parent.name}.")
    return np.int64(offset)

def check_chrono(attr_path: Path):
    rows, headers = read_csv(attr_path)
    timestamps = [np.int64(row[0]) for row in rows]
    chrono = True

    if not rows or not headers:
        logger.warning(f"There are no timestamps for {attr_path.stem}, skipping chronological check.")
        return chrono

    for i in range(1, len(timestamps)):
        if timestamps[i] < timestamps[i - 1]:
            chrono = False
            break
    
    logger.info(f"Timestamps for {attr_path.stem} are {'sorted' if chrono else 'not sorted'}.")

    return chrono

def sort_by_timestamp(attr_path: Path) -> None:
    rows, headers = read_csv(attr_path)

    if not rows or not headers:
        logger.warning(f"No data in {attr_path.stem}, skipping sort.")
        return

    try:
        sorted_rows = sorted(rows, key=lambda r: np.int64(r[0]))
    except Exception as e:
        logger.error(f"Error sorting {attr_path.name} by timestamp: {e}")
        return

    write_csv(attr_path, sorted_rows, headers)
    logger.info(f"Sorted {attr_path.stem} by timestamp.")

def check_duplicates(attr_path: Path):
    rows, headers = read_csv(attr_path)
    duplicate_found = False

    if not rows or not headers:
        logger.warning(f"There is no data in {attr_path.stem}, skipping duplicate check.")
        return False

    seen = set()
    duplicates = defaultdict(list)

    for i, row in enumerate(rows, start=1):
        row_tuple = tuple(row)
        if row_tuple in seen:
            duplicates[row_tuple].append(i)
            duplicate_found = True
        else:
            seen.add(row_tuple)

    logger.info(f"Timestamps for {attr_path.stem} {'have' if duplicate_found else 'do not have'} duplicates.")

    return duplicate_found

def remove_duplicates(attr_path: Path):
    rows, headers = read_csv(attr_path)

    if not rows or not headers:
        logger.warning(f"No data in {attr_path.name}, skipping duplicate removal.")
        return

    seen = set()
    unique_rows = []

    for row in rows:
        key = tuple(row)
        if key not in seen:
            seen.add(key)
            unique_rows.append(row)

    num_duplicates = len(rows) - len(unique_rows)
    
    if num_duplicates > 0:
        write_csv(attr_path, unique_rows, headers)
        logger.info(f"Removed {num_duplicates} duplicate rows from {attr_path.name}.")
    else:
        logger.info(f"No duplicates found in {attr_path.name}.")

def run(capture_path: Path, 
        session_id: str = None):
    
    if session_id == None:
        spot_sessions = []
        logger.info("No session_id provided, processing all spot sessions in the capture.")
        sessions_path = capture_path / 'sessions'
        sessions = [f for f in os.listdir(sessions_path) if os.path.isdir(os.path.join(sessions_path, f))]
        for session_id in sessions:
            if "spot" in session_id:
                spot_sessions.append(session_id)
    else:
        if "spot" not in session_id:
            logger.error(f"Session {session_id} is not spot session.")
        spot_sessions = [session_id]

    attributes = ['images', 'depths', 'imu', 'trajectories', 'wifi']

    for session_id in spot_sessions:
        
        path = capture_path / 'sessions' / session_id
                
        if "map" in session_id or "query" in session_id:
            logger.info(f"Skipping session {session_id} as it is a map or query session.")
            continue

        for attr in attributes:

            is_duplicates = check_duplicates(attr_path = path / f'{attr}.txt')
            if is_duplicates: remove_duplicates(attr_path = path / f'{attr}.txt')
            
            is_chronological = check_chrono(attr_path = path / f'{attr}.txt')
            if not is_chronological: sort_by_timestamp(attr_path = path / f'{attr}.txt')

            nano_to_micro_attr(attr_path = path / f'{attr}.txt')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     argument_default=argparse.SUPPRESS)
    
    parser.add_argument('--capture_path', type=Path, required=True, help='Path to the Capture directory.')
    parser.add_argument('--session_id', type=str, help='ID of the session to transform timestamps. If not provided, all sessions will be processed.')

    args = parser.parse_args().__dict__
    run(**args)
