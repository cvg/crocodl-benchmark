#!/bin/bash

# Flags and arguments:
# --description_path : path to the .txt file describing your model
# --{scene}_map_{map_device}_query_{query_device}_path : path to the .txt file containing poses estimated by your algorithm for
#       for given scene, map and query device
# --output_dir : path to the directory where final .zip is stored
# --capture_dir : path to the capture directory

# If you are using our data and the folder structure, script should work out-of-the-box just by alternating capture_dir
# To change folder structure depending on your method, you can change METHOD variables or directly line 44

SCENES=("hydro" "succu")
DEVICES=("ios" "hl" "spot")
#CAPTURE_DIR="/home/plukovic/research_assistant/capture"
CAPTURE_DIR="/media/plukovic/CVG 2TB NTFS/capture"
BENCHMARKING_DIR="benchmarking_ps"
DESCRIPTION_PATH="${CAPTURE_DIR}/codabench/desc.txt"
OUTPUT_DIR="${CAPTURE_DIR}/codabench"

KEYPOINT_METHOD="superpoint"
MATCHING_METHOD="lightglue"
EXTRACTION_METHOD="netvlad-10"

echo "Running combine_results_crocodl with arguments locally ..."
echo "python3 -m lamar.combine_results_crocodl \\"
echo "  --description_path \"$DESCRIPTION_PATH\" \\"

CMD="python3 -m lamar.combine_results_crocodl --description_path \"$DESCRIPTION_PATH\""

for scene in "${SCENES[@]}"; do
  if [[ "$scene" == "succu" ]]; then
    LOCATION_PATH="${CAPTURE_DIR}/SUCCULENT"
  else
    LOCATION_PATH="${CAPTURE_DIR}/${scene^^}"
  for map_device in "${DEVICES[@]}"; do
    for query_device in "${DEVICES[@]}"; do
      var_name="--${scene}_map_${map_device}_query_${query_device}_path"
      if [[ "$query_device" == "ios" ]]; then
        device_type="single_image"
      else
        device_type="rig"
      fi
      file_path="${LOCATION_PATH}/${BENCHMARKING_DIR}/pose_estimation/${query_device}_query/${map_device}_map/${KEYPOINT_METHOD}/${MATCHING_METHOD}/${EXTRACTION_METHOD}/triangulation/${device_type}/poses.txt"
      echo "  $var_name \"$file_path\" \\"
      CMD+=" ${var_name} \"${file_path}\""
    done
  done
done

CMD+=" --output_dir \"$OUTPUT_DIR\""
echo "  --output_dir \"$OUTPUT_DIR\""

# Uncomment the following line to actually run the script
eval "$CMD"

echo "Done, combine_results_crocodl completed."
