#!/bin/bash

INPUT_PATH="/home/plukovic/research_assistant/capture/HYDRO/raw/phone"
CAPTURE_PATH="/home/plukovic/research_assistant/capture/HYDRO"

echo "Running inside Docker..."

docker run --rm \
  -v "$INPUT_PATH":/data/input_dir \
  -v "$CAPTURE_PATH":/data/output_dir \
  croco:scantools \
  python3 -m scantools.run_spot_to_capture \
    --input_path /data/input_dir \
    --output_path /data/output_dir \
    --overwrite
    # --all_cameras

echo "Done, run_spot_to_capture.py process completed!"