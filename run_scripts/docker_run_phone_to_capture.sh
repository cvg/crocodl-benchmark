#!/bin/bash

# Flags and arguments:
# --input_path : path to the raw phone data directory
# --capture_path : path to the capture directory (where files are saved)

location="HYDRO"
INPUT_DIR="/home/plukovic/research_assistant/capture/HYDRO/raw/phone"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"

echo "Running run_phone_to_capture on $location inside a Docker ..."

docker run --rm \
  -v "$INPUT_DIR":/data/capture_dir \
  -v "$CAPTURE_DIR":/data/capture_dir \
  croco:scantools \
  python3 -m scantools.run_phone_to_capture \
    --input_path /data/capture_dir \
    --capture_path /data/input_dir \

echo "Done, run_phone_to_capture process completed on $location."
