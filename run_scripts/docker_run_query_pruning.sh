#!/usr/bin/env bash

# Flags and arguments:
# --capture_path : path to the capture directory
# --just_vis : only generates visuals

location="HYDRO"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"

echo "Running run_query_pruning on $location inside a Docker ..."

docker run --rm \
  -v "$CAPTURE_DIR":/data/capture_dir \
  croco:scantools \
  python -m scantools.run_query_pruning \
      --capture_path /data/capture_dir
  
echo "done, run_query_pruning process completed on $location."