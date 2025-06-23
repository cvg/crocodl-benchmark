#!/usr/bin/env bash

location="HYDRO"
INPUT_PATH="/home/plukovic/research_assistant/capture/HYDRO/raw/spot/merged"
CAPTURE_PATH="/home/plukovic/research_assistant/capture/${location}/"

echo "Running run_spot_to_capture on $location ..."

python3 -m scantools.run_spot_to_capture \
    --input_path $INPUT_PATH \
    --output_path $CAPTURE_PATH \
    --overwrite
    # --all_cameras

echo "Done, run_spot_to_capture process completed on $location."
