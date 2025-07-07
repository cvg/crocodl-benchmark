#!/bin/bash

# Flags and arguments:
# --capture_path : path to capture directory
# --{device}{m/q} : generate {m/q} for the {device}
# --transform : generate 4DOF transformation and transform trajectories
# --just_vis : only generate visualizations and files, without overwriting

location="HYDRO"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"

echo "Running run_map_query_split_manual on $location inside a Docker ..."

docker run --rm \
  -v "$CAPTURE_PATH":/data/input_dir \
  croco:scantools \
  python3 -m scantools.run_map_query_split_manual \
      --capture_path /data/input_dir \
      --iosm --iosq --hlq --hlm --spotq --spotm \
      --transform \
      #--just_vis

echo "Done, run_map_query_split_manual process completed on $location."
