#!/bin/bash

location="HYDRO"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"

echo "Running map/query split inside Docker..."

docker run --rm \
  -v "$CAPTURE_PATH":/data/input_dir \
  croco:scantools \
  python3 -m scantools.run_map_query_split_manual \
      --capture_path /data/input_dir \
      --iosm --iosq --hlq --hlm --spotq --spotm

echo "Done, run_map_query_split_manual process completed!"
