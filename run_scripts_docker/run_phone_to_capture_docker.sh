#!/bin/bash

INPUT_PATH="/home/plukovic/research_assistant/capture/HYDRO/raw/phone"
CAPTURE_PATH="/home/plukovic/research_assistant/capture/HYDRO"

echo "Running merge inside Docker..."

docker run --rm \
  -v "$INPUT_PATH":/data/capture_dir \
  -v "$CAPTURE_PATH":/data/input_dir \
  croco:scantools \
  python3 -m scantools.run_phone_to_capture \
    --input_path /data/capture_dir \
    --capture_path /data/input_dir \
    #--visualize 

echo "Done, run_phone_to_capture process completed!"
