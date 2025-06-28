#!/usr/bin/env bash

location="HYDRO"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"

echo "Running run_visualize_query_renders on $location ..."

docker run --rm \
  -v "$CAPTURE_DIR":/data/capture_dir \
  croco:scantools \
  python3 -m scantools.run_visualize_query_renders \
    --capture_path "$CAPTURE_DIR" \
    --skip "10" \
    --simplified_mesh

echo "Done, run_visualize_query_renders process completed for $location."