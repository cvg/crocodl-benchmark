#!/usr/bin/env bash

# Flags and arguments:
# --capture_path : path to capture directory
# --{device} : flags that need to be set to visualize map query split for specific device

location="ARCHE_B5"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"

echo "Running run_visualize_trajectories on $location ..."

python3 -m scantools.run_visualize_trajectories \
  --capture_path "$CAPTURE_DIR" \
  --ios --spot --hl \ 

echo "Done, run_visualize_trajectories process completed for $location."