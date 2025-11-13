#!/bin/bash

# Flags and arguments:
# --description_path : path to the .txt file describing your model
# --{scene}_map_{map_device}_query_{query_device}_path : path to the .txt file containing poses estimated by your algorithm for
#       for given scene, map and query device
# --output_dir : path to the directory where final .zip is stored
# --capture_dir : path to the capture directory

# If you are using our data and the folder structure, script should work out-of-the-box just by alternating capture_dir
# To change folder structure depending on your method, you can change METHOD variables or directly line 44

if [ -z "$CAPTURE_DIR" ]; then
  echo "[ERROR] CAPTURE_DIR env var not set. Make sure to export CAPTURE_DIR=/path/to/data/root."
  exit 1
fi

BENCHMARKING_DIR="/long/benchmarking_results"
DESCRIPTION_FILE="${CAPTURE_DIR}/codabench/desc.txt"
OUTPUT_DIR="${CAPTURE_DIR}/codabench"
LOCAL_FEATURE_METHOD="superpoint"
MATCHING_METHOD="lightglue"
GLOBAL_FEATURE_METHOD="megaloc"
SCENES=("ARCHE_D2")
DEVICES_MAP=("ios" "hl" "spot")
DEVICES_QUERY=("ios" "hl" "spot")

echo "You are running with parameters: "
echo "  Capture: ${CAPTURE_DIR}"
echo "  Output: ${OUTPUT_DIR}"
echo "  Model description file: ${DESCRIPTION_FILE}"
echo "  Benchmarking dir: ${BENCHMARKING_DIR}"
echo "  Local feature method: ${LOCAL_FEATURE_METHOD}"
echo "  Matching method: ${MATCHING_METHOD}"
echo "  Global feature method: ${GLOBAL_FEATURE_METHOD}"
echo "  Scenes: ${SCENES[@]}"
echo "  Devices map: ${DEVICES_MAP[@]}"
echo "  Devices query: ${DEVICES_QUERY[@]}"


# read -p "Do you want to continue? (y/n): " answer

# if [[ ! "$answer" =~ ^[Yy]$ ]]; then
#     echo "Execution aborted."
#     exit 1
# fi

echo "Running combine_results_crocodl inside Docker ..."
echo "docker run --rm"
echo "-v "$CAPTURE_DIR":/data/capture_dir"
echo "-v "$DESCRIPTION_FILE":/data/capture_dir/codabench/desc.txt"
echo "croco:lamar"
echo "python3 -m lamar.combine_results_crocodl \\"
echo "  --description_path /data/capture_dir/codabench/desc.txt \\"

CMD=(python3 -m lamar.combine_results_crocodl --description_path /data/capture_dir/codabench/desc.txt)

for scene in "${SCENES[@]}"; do
  if [[ "$scene" == "succu" ]]; then
    LOCATION_PATH="/data/capture_dir/SUCCULENT"
  else
    LOCATION_PATH="/data/capture_dir/${scene^^}"
  fi

  for map_device in "${DEVICES_MAP[@]}"; do
    for query_device in "${DEVICES_QUERY[@]}"; do
      var_name="--${scene}_map_${map_device}_query_${query_device}_path"
      if [[ "$query_device" == "ios" ]]; then
        device_type="single_image"
      else
        device_type="rig"
      fi
      file_path="${LOCATION_PATH}/${BENCHMARKING_DIR}/pose_estimation/${query_device}_query/${map_device}_map/${LOCAL_FEATURE_METHOD}/${MATCHING_METHOD}/${GLOBAL_FEATURE_METHOD}/triangulation/${device_type}/poses.txt"

      echo "  $var_name \"$file_path\" \\"
      CMD+=("${var_name}" "${file_path}")
    done
  done
done

CMD+=(--output_dir /data/capture_dir/codabench)

echo "  --output_dir \"$OUTPUT_DIR\""

docker run --rm \
  -v "$CAPTURE_DIR":/data/capture_dir \
  -v "$DESCRIPTION_FILE":/data/capture_dir/codabench/desc.txt \
  croco:long \
  "${CMD[@]}"

echo "Done, combine_results_crocodl completed."
