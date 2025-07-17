#!/usr/bin/env bash

# Flags and arguments:
# --capture_path : path to capture directory

# This script will run matrix visualization on all combinations of given devices.
# You can tune it to your liking, or just run it once with wanted flags.

if [ -z "$CAPTURE_DIR" ]; then
  echo "[ERROR] CAPTURE_DIR env var not set. Make sure to export CAPTURE_DIR=/path/to/data/root."
  exit 1
fi

if [ -z "$LOCATION" ]; then
  echo "[ERROR] LOCATION env var not set. Make sure to export LOCATION=location."
  exit 1
fi

CAPTURE="${CAPTURE_DIR}/${LOCATION}"
FLAGS=(--ios --spot --hl)

echo "You are running with parameters: "
echo "  Capture: ${CAPTURE}"
echo "  Flags: ${FLAGS[@]}"

read -p "Do you want to continue? (y/n): " answer

if [[ ! "$answer" =~ ^[Yy]$ ]]; then
    echo "Execution aborted."
    exit 1
fi

echo "Running run_visualize_map_query_matrix with all combinations of 2 and 3 FLAGS on location {$LOCATION} inside a Docker ..."

# All 2-combinations
for ((i=0; i<${#FLAGS[@]}-1; i++)); do
  for ((j=i+1; j<${#FLAGS[@]}; j++)); do
    echo "Running run_visualize_map_query_matrix with FLAGS: ${FLAGS[i]} ${FLAGS[j]} ..."
    docker run --rm \
      -v "$CAPTURE":/data/capture_dir \
      croco:scantools \
      python3 -m scantools.run_visualize_map_query_matrix \
        --capture_path /data/capture_dir \
        "${FLAGS[i]}" "${FLAGS[j]}"
    echo "Done, run_visualize_map_query_matrix process completed with FLAGS: ${FLAGS[i]} ${FLAGS[j]}."
  done
done

# 3-combination
echo "Running run_visualize_map_query_matrix with FLAGS: ${FLAGS[*]} ..."
docker run --rm \
  -v "$CAPTURE":/data/capture_dir \
  croco:scantools \
  python3 -m scantools.run_visualize_map_query_matrix \
    --capture_path /data/capture_dir \
    "${FLAGS[@]}"
echo "Done, run_visualize_map_query_matrix process completed with FLAGS: ${FLAGS[*]}."

echo "Done, run_visualize_map_query_matrix with all combinations of 2 and 3 FLAGS on $LOCATION."