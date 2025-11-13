import os
import shutil
import pandas as pd
import numpy as np


def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        lines = [line.strip() for line in lines]
    return lines

def write_file(file_path, lines):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as  f:
        for line in lines:
            f.write(line + '\n')

def extract_proc(session_dir, map_endpoint_dir, file_name="proc/subsessions.txt"):
    src_path = os.path.join(session_dir, file_name)
    des_path = os.path.join(map_endpoint_dir, file_name)
    
    os.makedirs(os.path.dirname(des_path), exist_ok=True)
    shutil.copyfile(src_path, des_path)
    
def sample_evenly(group, ext_percent):
    n = len(group)
    k = max(1, round(ext_percent * n))  # at least one
    if k >= n:
        return group
    indices = np.linspace(0, n - 1, k, dtype=int)
    return group.iloc[indices]

def get_map_info(session_dir, ext_percent=0.3):
    file_name = 'images.txt'
    file_path = os.path.join(session_dir, file_name)
    
    df = pd.read_csv(file_path, sep=", ", engine="python")
    df['subsession'] = df['sensor_id'].apply(lambda x: x.split("/")[0])
    
    id_df = df[["# timestamp", "subsession"]].drop_duplicates()
    id_df = id_df.groupby('subsession', group_keys=False).apply(lambda group: sample_evenly(group, ext_percent), include_groups=False)
    map_ids = id_df["# timestamp"].values
    
    # Get all image paths for the selected map IDs
    map_df = df[df['# timestamp'].isin(map_ids)]
    map_image_paths = map_df['image_path'].values
    
    return map_ids, map_image_paths

def verify_line(line, map_ids, key_index, splitter="_"):
    idx = line.split(", ")[0].split("/")[-1].split(splitter)[key_index]
    if idx.isnumeric() and int(idx) in map_ids:
        return True
    if not idx.isnumeric():
        return True
    return False

def extract_file(session_dir, map_endpoint_dir, map_ids, file_name, key_index, splitter):
    src_path = os.path.join(session_dir, file_name)
    des_path = os.path.join(map_endpoint_dir, file_name)
    
    lines = []
    ori_lines =  read_file(src_path)
    for line in ori_lines:
        if verify_line(line, map_ids, key_index, splitter):
            lines.append(line)
    
    write_file(des_path, lines)
    
def extract_txt(session_dir, map_endpoint_dir, map_ids, device):
    key_index = -1
    splitter = "_"
    extract_file(session_dir, map_endpoint_dir, map_ids, "images.txt", key_index=key_index, splitter=splitter)
    extract_file(session_dir, map_endpoint_dir, map_ids, "sensors.txt", key_index=key_index, splitter=splitter)
    extract_file(session_dir, map_endpoint_dir, map_ids, "trajectories.txt", key_index=key_index, splitter=splitter)
    
    if device in ['hl', 'spot']:
        if device == 'spot':
            key_index = 0
            splitter = "-"
        extract_file(session_dir, map_endpoint_dir, map_ids, "rigs.txt", key_index=key_index, splitter=splitter)          

def extract_raw(session_dir, map_endpoint_dir, map_image_paths, raw_dir="raw_data"):
    session_raw_dir = os.path.join(session_dir, raw_dir)
    map_raw_dir = os.path.join(map_endpoint_dir, raw_dir)
    
    # Process each map image path directly
    for relative_image_path in map_image_paths:
        # Build full source path
        source_path = os.path.join(session_raw_dir, relative_image_path)
        dest_path = os.path.join(map_raw_dir, relative_image_path)
        # Check if the source file exists
        if os.path.exists(source_path):
            # Create destination directory
            dest_dir = os.path.dirname(dest_path)
            os.makedirs(dest_dir, exist_ok=True)
            
            # Copy the file
            shutil.copyfile(source_path, dest_path, follow_symlinks=True)

def extract_map(session_dir, map_endpoint_dir, ext_percent=0.3, symlinks=True):
    device = map_endpoint_dir.split('/')[-1].split('_map')[0]
    '''
    SAME: 
        proc/subsessions.txt
    SPLIT: by id (timestamps)
        sensors.txt (only ios is diff)
        images.txt
        trajectories.txt
        rigs.txt (for hl and spot)
    RAW: move by id
    '''
    # PROC
    extract_proc(session_dir,  map_endpoint_dir)
    
    map_ids, map_image_paths = get_map_info(session_dir, ext_percent)
    print(f"--> {device}_map len = {len(map_image_paths)}")
    
    # .TXT
    extract_txt(session_dir, map_endpoint_dir, map_ids, device)
    
    # RAW
    extract_raw(session_dir, map_endpoint_dir, map_image_paths)
    
    print("DONE", map_endpoint_dir)