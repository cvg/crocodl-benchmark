#!/usr/bin/env bash

location="HYDRO"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"

echo "Running run_visualize_map_query on $location ..."

python3 -m scantools.run_visualize_map_query \
  --capture_path "$CAPTURE_DIR" \
  --ios \
  --spot \
  --hl 

echo "Done, run_visualize_map_query process completed on $location."