#!/bin/bash

# Flags and arguments:
# --input_path : path to the merged spot bagfiles directory
# --output_path : path to the output directory
# --overwrite : overwrite existing sessions

location="HYDRO"
INPUT_DIR="/home/plukovic/research_assistant/capture/HYDRO/raw/phone"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"

echo "Running run_spot_to_capture on $location inside a Docker ..."

docker run --rm \
  -v "$INPUT_DIR":/data/input_dir \
  -v "$CAPTURE_DIR":/data/output_dir \
  croco:scantools \
  python3 -m scantools.run_spot_to_capture \
    --input_path /data/input_dir \
    --output_path /data/output_dir \
    --overwrite \

echo "Done, run_spot_to_capture.py process completed on $location."