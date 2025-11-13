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

if [ -z "$CAPTURE_DIR" ]; then
  echo "[ERROR] CAPTURE_DIR env var not set. Make sure to export CAPTURE_DIR=/path/to/data/root."
  exit 1
fi

LOCATIONS=("ARCHE_D2")
OUTPUT_DIR="long/benchmarking_results"
QUERIES_FILE="keyframes_original.txt"
LOCAL_FEATURE_METHOD="superpoint"
MATCHING_METHOD="lightglue"
GLOBAL_FEATURE_METHOD="megaloc"
DEVICES_REF=("ios" "hl" "spot")
DEVICES_QUERY=("ios" "hl" "spot")
R_THRESHOLD=20.0
T_THRESHOLD=20.0
TOP=5
R_MARGIN=5 # margin that split low and high rotation error.

echo "You are running with parameters: "
echo "  Capture: ${CAPTURE_DIR}"
echo "  Output: ${OUTPUT_DIR}"
echo "  Locations: ${LOCATIONS[@]}"
echo "  Queries file: ${QUERIES_FILE}"
echo "  Local feature method: ${LOCAL_FEATURE_METHOD}"
echo "  Matching method: ${MATCHING_METHOD}"
echo "  Global feature method: ${GLOBAL_FEATURE_METHOD}"
echo "  Reference devices: ${DEVICES_REF[@]}"
echo "  Query devices: ${DEVICES_QUERY[@]}"

# read -p "Do you want to continue? (y/n): " answer

# if [[ ! "$answer" =~ ^[Yy]$ ]]; then
#     echo "Execution aborted."
#     exit 1
# fi

for LOCATION in "${LOCATIONS[@]}"; do

  CAPTURE="${CAPTURE_DIR}/${LOCATION}"
  OUTPUT_DIR_LOCATION="${CAPTURE}/${OUTPUT_DIR}"

  # Do not remove or change this line if you intend to use automatic recall reading tool.
  echo "Starting cross validate for scene: $LOCATION and queries file: $QUERIES_FILE"

  for ref in "${DEVICES_REF[@]}"; do
    for query in "${DEVICES_QUERY[@]}"; do
      echo "Running with ref_id=${ref}_map and query_id=${query}_query ..."
      
      is_rig_flag=""
      if [[ "$query" == "hl" || "$query" == "spot" ]]; then
        is_rig_flag="--is_rig"
        echo "Run is using flag --is_rig due to ${query}_query"
      fi

      python -m lamar.cross_valid \
        --scene "$SCENE" \
        --ref_id "${ref}_map" \
        --query_id "${query}_query" \
        --retrieval "$GLOBAL_FEATURE_METHOD" \
        --feature "$LOCAL_FEATURE_METHOD" \
        --matcher "$MATCHING_METHOD" \
        --capture "$CAPTURE" \
        --outputs "$OUTPUT_DIR_LOCATION" \
        --query_filename "$QUERIES_FILE" \
        --R_threshold "$R_THRESHOLD" \
        --t_threshold "$T_THRESHOLD" \
        --top "$TOP" \
        --r_margin "$R_MARGIN" \
        $is_rig_flag

      echo "Cross validating completed for ref_id=${ref}_map and query_id=${query}_query"
      echo ""
    done
  done

  echo -e "Cross validating completed for scene: $LOCATION and queries file: $QUERIES_FILE" 
  echo ""
  echo ""
done
