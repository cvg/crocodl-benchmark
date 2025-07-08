#!/usr/bin/env bash

# Flags and arguments:
# --capture_path : path to capture directory
# --{device} : flags that need to be set to visualize map query split for specific device

location="HYDRO"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"

echo "Running run_visualize_trajectories on location $location inside a Docker ..."

docker run --rm \
  -v "$CAPTURE_DIR":/data/capture_dir \
  croco:scantools \
  python3 -m scantools.run_visualize_trajectories \
    --capture_path /data/capture_dir  \
    --ios --spot --hl

echo "Done, run_visualize_trajectories process completed on $location."