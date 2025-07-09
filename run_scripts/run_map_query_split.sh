#!/usr/bin/env bash

# Flags and arguments:
# --capture_path : path to capture directory
# --{device}{m/q} : generate {m/q} for the {device}
# --transform : generate 4DOF transformation and transform trajectories
# --just_viz : only generate visualizations and files, without overwriting

location="ARCHE_B3"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"

echo "Running run_map_query_split_manual on $location ..."

python -m scantools.run_map_query_split_manual \
      --capture_path "$CAPTURE_DIR" \
      --iosm --iosq --hlq --hlm --spotq --spotm \
      --transform \
#      --just_vis
  
echo "Done, run_map_query_split_manual process completed on $location."