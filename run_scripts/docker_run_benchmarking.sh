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

location="HYDRO"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"
OUTPUT_DIR="${CAPTURE_DIR}/benchmarking_og"

devices=(spot ios hl)

echo "Running benchmarking on $location inside a Docker ..."

for ref in "${devices[@]}"; do
  for query in "${devices[@]}"; do
    echo "Running with ref_id=${ref}_map and query_id=${query}_query ..."
    docker run --rm \
      -v "$OUTPUT_DIR":/data/output_dir \
      -v "$CAPTURE_DIR":/data/capture_dir \
      croco:lamar \
      python -m lamar.run \
        --scene "$SCENE" \
        --ref_id "${ref}_map" \
        --query_id "${query}_query" \
        --retrieval netvlad \
        --feature superpoint \
        --matcher lightglue \
        --capture /data/capture_dir \
        --outputs /data/output_dir
    echo "Done, benchmarking completed for ref_id=${ref}_map and query_id=${query}_query."
  done
done

echo "Done, benchmarking process completed on $location."