#!/usr/bin/env python3
import os
import time
import argparse
from huggingface_hub import snapshot_download
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

def main():
    p = argparse.ArgumentParser(description="Scoped download of session folders from a HF dataset.")
    p.add_argument("--repo_id", required=True, help="Dataset repo id, e.g. CroCoDL/ARCHE_D2")
    p.add_argument("--allow_patterns", required=True, nargs="+", type=str, help="Default is 'sessions' or 'sessions registration ...'")
    p.add_argument("--local_dir", required=True, help="Local dir to save into")
    args = p.parse_args()

    allow_patterns = []
    for pattern in args.allow_patterns:
        allow_patterns.append(f"{pattern}/**")
            
    max_retries = 5
    retry = 0
    while True:
        try:
            print("Downloading selected directories...")
            snapshot_download(
                repo_id=args.repo_id,
                repo_type="dataset",
                local_dir=args.local_dir,
                allow_patterns=allow_patterns,
                force_download=True,
                token=os.getenv("HF_TOKEN")
            )
            print(f"Done. Saved to: {args.local_dir}")
            retry = 0
        except Exception as e:
            print(f"[Exception] {e}")
            retry += 1
            if retry > max_retries:
                break
            print(f"===================== RETRY {retry}/{max_retries} =====================")
            for i in tqdm(range(333), unit="s", desc="Waiting: "):
                time.sleep(1)
                
if __name__ == "__main__":
    main()
