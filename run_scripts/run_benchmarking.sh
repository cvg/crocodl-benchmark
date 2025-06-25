#!/bin/bash

location="HYDRO"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"
OUTPUT="${CAPTURE_DIR}/benchmarking"

devices=(ios spot hl)

echo "Starting benchmarking for scene: $location"

for ref in "${devices[@]}"; do
  for query in "${devices[@]}"; do
    echo "Running with ref_id=${ref}_map and query_id=${query}_query ..."
    python -m lamar.run \
      --scene "$SCENE" \
      --ref_id "${ref}_map" \
      --query_id "${query}_query" \
      --retrieval netvlad \
      --feature superpoint \
      --matcher lightglue \
      --capture "$CAPTURE_DIR" \
      --outputs "$OUTPUT" \
      --query_filename "keyframes_original.txt"
    echo "Benchmarking completed for ref_id=${ref}_map and query_id=${query}_query"
    echo ""
  done
done

echo "Benchmarking completed for scene: $location"