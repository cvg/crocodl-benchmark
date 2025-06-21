#!/usr/bin/env bash

INPUT_PATH="/home/plukovic/research_assistant/capture/HYDRO/raw/navvis"
CAPTURE_PATH="/home/plukovic/research_assistant/capture/HYDRO"

echo "Running pipeline_scans.py ..."

python3 -m pipelines.pipeline_scans \
    --input_path $INPUT_PATH \
    --capture_path $CAPTURE_PATH \
    --sessions "2023-11-03_10.31.58" "2023-11-03_13.51.06" \
    --num_workers 2

echo "Done, pipeline_scans.py process completed!"
