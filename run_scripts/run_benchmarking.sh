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

# If you are saving to a .txt file you might use our run_scripts/run_read_benchmarking_output.sh script.
# This will print out confusion matrices of benchamrking results only of recall and map/query names.

location="ARCHE_B3"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"
OUTPUT="${CAPTURE_DIR}/benchmarking_og"
QUERIES_FILE="keyframes_original.txt"

devices_ref=(spot ios hl)
device_query=(spot ios hl)

# Do not remove or change this line if you intend to use automatic recall reading tool.
echo "Starting benchmarking for scene: $location and queries file: $QUERIES_FILE"

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
      --query_filename "$QUERIES_FILE" \
      $is_rig_flag

    echo "Benchmarking completed for ref_id=${ref}_map and query_id=${query}_query"
    echo ""
  done
done

echo -e "Benchmarking completed for scene: $location and queries file: $QUERIES_FILE"

OUTPUT="${CAPTURE_DIR}/benchmarking_ps"
QUERIES_FILE="keyframes_pruned_subsampled.txt"

# Do not remove or change this line if you intend to use automatic recall reading tool.
echo "Starting benchmarking for scene: $location and queries file: $QUERIES_FILE"

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
      --query_filename "$QUERIES_FILE" \
      $is_rig_flag

    echo "Benchmarking completed for ref_id=${ref}_map and query_id=${query}_query"
    echo ""
  done
done

echo -e "Benchmarking completed for scene: $location and queries file: $QUERIES_FILE"