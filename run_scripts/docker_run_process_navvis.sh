#!/bin/bash

INPUT_PATH="/home/plukovic/research_assistant/capture/HYDRO/raw/navvis"
CAPTURE_PATH="/home/plukovic/research_assistant/capture/HYDRO"

echo "Running navvis process inside Docker..."

docker run --rm \
  -v "$INPUT_PATH":/data/capture_dir \
  -v "$CAPTURE_PATH":/data/input_dir \
  croco:scantools \
  python3 -m pipelines.pipeline_scans \
      --input_path /data/input_dir \
      --capture_path /data/capture_dir \
      --sessions "2023-11-03_10.31.58" "2023-11-03_13.51.06" \
      --num_worksers_mesh 2

echo "Done, pipeline_scans process completed!"
