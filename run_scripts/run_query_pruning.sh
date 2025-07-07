#!/usr/bin/env bash

# Flags and arguments:
# --capture_path : path to the capture directory
# --just_vis : only generates visuals

location="ARCHE_B5"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"

echo "Running run_query_pruning on $location ..."

python -m scantools.run_query_pruning \
      --capture_path "$CAPTURE_DIR" \
#      --just_vis
  
echo "Done, run_query_pruning process completed on $location."
