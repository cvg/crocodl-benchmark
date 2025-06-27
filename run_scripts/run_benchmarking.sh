#!/bin/bash

location="HYDRO"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"
OUTPUT="${CAPTURE_DIR}/benchmarking_og"

devices_ref=(hl spot ios)
device_query=(hl spot ios)

echo "Starting benchmarking for scene: $location"

for ref in "${devices_ref[@]}"; do
  for query in "${device_query[@]}"; do
    echo "Running with ref_id=${ref}_map and query_id=${query}_query ..."
    
    is_rig_flag=""
    if [[ "$query" == "hl" || "$query" == "spot" ]]; then
      is_rig_flag="--is_rig"
      echo "Run is using flag --is_rig due to ${query}_query"
    fi

    python -m lamar.run \
      --scene "$SCENE" \
      --ref_id "${ref}_map" \
      --query_id "${query}_query" \
      --retrieval netvlad \
      --feature superpoint \
      --matcher lightglue \
      --capture "$CAPTURE_DIR" \
      --outputs "$OUTPUT" \
      --query_filename "keyframes_original.txt" \
      $is_rig_flag

    echo "Benchmarking completed for ref_id=${ref}_map and query_id=${query}_query"
    echo ""
  done
done

echo "Benchmarking completed for scene: $location"

OUTPUT="${CAPTURE_DIR}/benchmarking_ps"

echo "Starting benchmarking for scene: $location"

for ref in "${devices_ref[@]}"; do
  for query in "${device_query[@]}"; do
    echo "Running with ref_id=${ref}_map and query_id=${query}_query ..."
    
    is_rig_flag=""
    if [[ "$query" == "hl" || "$query" == "spot" ]]; then
      is_rig_flag="--is_rig"
      echo "Run is using flag --is_rig due to ${query}_query"
    fi

    python -m lamar.run \
      --scene "$SCENE" \
      --ref_id "${ref}_map" \
      --query_id "${query}_query" \
      --retrieval netvlad \
      --feature superpoint \
      --matcher lightglue \
      --capture "$CAPTURE_DIR" \
      --outputs "$OUTPUT" \
      --query_filename "keyframes_pruned_subsampled.txt" \
      $is_rig_flag

    echo "Benchmarking completed for ref_id=${ref}_map and query_id=${query}_query"
    echo ""
  done
done

echo "Benchmarking completed for scene: $location"