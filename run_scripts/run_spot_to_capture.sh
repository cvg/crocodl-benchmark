#!/usr/bin/env bash

# Flags and arguments:
# --input_path : path to the merged spot bagfiles directory
# --output_path : path to the output directory
# --overwrite : overwrite existing sessions

location="HYDRO"
INPUT_DIR="/home/plukovic/research_assistant/capture/HYDRO/raw/spot/merged"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"

echo "Running run_spot_to_capture on $location ..."

python3 -m scantools.run_spot_to_capture \
    --input_path $INPUT_DIR \
    --output_path $CAPTURE_DIR \
    --overwrite

echo "Done, run_spot_to_capture process completed on $location."
