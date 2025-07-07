#!/usr/bin/env bash

# Flags and arguments:
# --input_path : path to the raw phone data directory
# --capture_path : path to the capture directory (where files are saved)
# --sessions : list of sessions to be merged together into a single navvis session
# --num_workers_mesh: number of processing cores to be used for merging

# If you are using this script, please consider that it uses a lot of RAM since it has to load meshes.

location="HYDRO"
INPUT_PATH="/home/plukovic/research_assistant/capture/HYDRO/raw/navvis"
CAPTURE_PATH="/home/plukovic/research_assistant/capture/${location}/"

echo "Running pipeline_scans on $location ..."

python3 -m pipelines.pipeline_scans \
    --input_path $INPUT_PATH \
    --capture_path $CAPTURE_PATH \
    --sessions "2023-11-03_10.31.58" "2023-11-03_13.51.06" \
    --num_workers 2

echo "Done, pipeline_scans.py process completed on $location."
