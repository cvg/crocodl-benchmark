#!/usr/bin/env bash

# Flags and arguments:
# --input_path : path to the raw phone data directory
# --capture_path : path to the capture directory (where files are saved)
# --sessions : list of sessions to be merged together into a single navvis session
# --num_workers_mesh: number of processing cores to be used for merging

# If you are using this script, please consider that it uses a lot of RAM since it has to load meshes.

if [ -z "$CAPTURE_DIR" ]; then
  echo "[ERROR] CAPTURE_DIR env var not set. Make sure to export CAPTURE_DIR=/path/to/data/root."
  exit 1
fi

if [ -z "$LOCATION" ]; then
  echo "[ERROR] LOCATION env var not set. Make sure to export LOCATION=location."
  exit 1
fi

CAPTURE="${CAPTURE_DIR}/${LOCATION}"
INPUT_DIR="${CAPTURE}/raw/phone"
SESSIONS=("2023-11-03_10.31.58" "2023-11-03_13.51.06")

echo "You are running with parameters: "
echo "  Capture: ${CAPTURE}"
echo "  Input path: ${INPUT_DIR}"
echo "  Sessions: ${SESSIONS[@]}"

read -p "Do you want to continue? (y/n): " answer

if [[ ! "$answer" =~ ^[Yy]$ ]]; then
    echo "Execution aborted."
    exit 1
fi

echo "Running pipeline_scans on $LOCATION ..."

python3 -m pipelines.pipeline_scans \
    --input_path $INPUT_DIR \
    --capture_path $CAPTURE \
    --sessions "${SESSIONS[@]}" \
    --num_workers 2

echo "Done, pipeline_scans.py process completed on $LOCATION."
