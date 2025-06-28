#!/usr/bin/env bash

location="HYDRO"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"
QUERY_ID="ios_query"

echo "Running run_visualize_query_renders on $location ..."

python3 -m scantools.run_visualize_query_renders \
  --capture_path "$CAPTURE_DIR" \
  --skip "10" \
  --simplified_mesh

echo "Done, run_visualize_query_renders process completed for $location."