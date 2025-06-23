#!/bin/bash

location="HYDRO"
INPUT_DIR="/home/plukovic/research_assistant/capture/HYDRO/raw/navvis"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"

echo "Running pipeline_scans on $location inside a Docker ..."

docker run --rm \
  -v "$INPUT_DIR":/data/input_dir \
  -v "$CAPTURE_DIR":/data/capture_dir \
  croco:scantools \
  python3 -m pipelines.pipeline_scans \
      --input_path /data/input_dir \
      --capture_path /data/capture_dir \
      --sessions "2023-11-03_10.31.58" "2023-11-03_13.51.06" \
      --num_worksers_mesh 2

echo "Done, pipeline_scans process completed on $location."
