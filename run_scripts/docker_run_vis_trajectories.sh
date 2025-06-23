#!/usr/bin/env bash

location="HYDRO"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"

echo "Running run_visualize_trajectories on location $location inside a Docker ..."

docker run --rm \
  -v "$CAPTURE_DIR":/data/capture_dir \
  croco:scantools \
  python3 -m scantools.run_visualize_trajectories \
    --capture_path /data/capture_dir  \
    --ios \
    --spot \
    --hl 

echo "Done, run_visualize_trajectories process completed on $location."