import yaml
import argparse
from pathlib import Path
import os
import shutil

from .scripts.extract_location import extract_location


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a reduced capture")
    parser.add_argument("--config", default="./extract_capture_cv/config.yaml", type=Path, help="YAML configuration file")
    return parser.parse_args()

def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    f.close()
    return config

def extract_capture(config):
    capture_dir = config['capture_dir']
    endpoint = config['capture_subset_dir']
    map_ep = config['map_ep']
    query_ep = config['query_ep']
    
    locations = sorted(os.listdir(capture_dir))
    for location in locations:
        if location in ['codabench']:
            ori_coda_dir = os.path.join(capture_dir, "codabench")
            new_coda_dir = os.path.join(endpoint, "codabench")
            os.makedirs(new_coda_dir, exist_ok=True)
            
            files = os.listdir(ori_coda_dir)
            for file in files:
                if file == 'desc.txt':
                    src_path = os.path.join(ori_coda_dir, file)
                    dst_path = os.path.join(new_coda_dir, file)

                    shutil.copy(src_path, dst_path, follow_symlinks=True)
            print(f'DONE {new_coda_dir}')
            continue
        location_dir = os.path.join(capture_dir, location)
        endpoint_dir = os.path.join(endpoint, location)
        
        extract_location(location_dir, endpoint_dir, map_ep, query_ep)

def main():
    args = parse_args()
    config_path = args.config.resolve()
    config = load_config(config_path)
    extract_capture(config)
    
if __name__ == '__main__':
    main()