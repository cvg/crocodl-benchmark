#!/bin/bash

# Flags and arguments:
# --scene : name of the scene, all capital leters
# --ref_id : name of the map session
# --query_id : name of the query session
# --retrieval : retrieval method
# --feature : feature extraction method
# --matcher : feature matcher method
# --capture : path to capture directory
# --outputs : path to the ouput directory
# --query_filename : name of the file keyframes list, in query_name/proc/query_filename.txt
# --is_rig : to be used with rig like query sessions, i.e. hololens and spot

# Consider writing output of this script in a file if you are using full configuration (all 18 configurations). 
# Output is too long, you will not be able to see all the recall results inside a CLI! Something like this:
# ./run_scripts/run_benchmarking.sh > location.txt 2>&1

location="ARCHE_GRANDE"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"
OUTPUT="${CAPTURE_DIR}/benchmarking_og"

devices_ref=(spot ios hl)
device_query=(spot ios hl)

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