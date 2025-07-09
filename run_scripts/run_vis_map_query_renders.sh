#!/usr/bin/env bash

# Flags and arguments:
# --capture_path : path to the capture directory
# --skip : this is the subsampling rate of the rendering
# --num_workers : number of processing cores used for rendering
# --save_video : save rendering comparisons in form of a video
# --simplified_mesh : use simplified mesh (uses less RAM)

# Consider using --simplified_mesh flag if you have less that 32GB RAM. Most of the locations 
# would not run with less than 32GB RAM.

location="ARCHE_B3"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"

echo "Running run_visualize_map_query_renders on $location ..."

python3 -m scantools.run_visualize_map_query_renders \
  --capture_path "$CAPTURE_DIR" \
  --skip "10" \
  --num_workers 4 \
  --save_video \
  --simplified_mesh \

echo "Done, run_visualize_map_query_renders process completed for $location."
