#!/bin/bash

# Flags and arguments:
# --input_path : path to the merged spot bagfiles directory
# --output_path : path to the output directory
# --overwrite : overwrite existing sessions

if [ -z "$CAPTURE_DIR" ]; then
  echo "[ERROR] CAPTURE_DIR env var not set. Make sure to export CAPTURE_DIR=/path/to/data/root."
  exit 1
fi

if [ -z "$LOCATION" ]; then
  echo "[ERROR] LOCATION env var not set. Make sure to export LOCATION=location."
  exit 1
fi

CAPTURE="${CAPTURE_DIR}/${LOCATION}"
INPUT_DIR="${CAPTURE}/raw/spot/merged"

echo "You are running with parameters: "
echo "  Capture: ${CAPTURE}"
echo "  Input path: ${INPUT_DIR}"

read -p "Do you want to continue? (y/n): " answer

if [[ ! "$answer" =~ ^[Yy]$ ]]; then
    echo "Execution aborted."
    exit 1
fi

echo "Running run_spot_to_capture on $LOCATION inside a Docker ..."

docker run --rm \
  -v "$INPUT_DIR":/data/input_dir \
  -v "$CAPTURE":/data/output_dir \
  croco:scantools \
  python3 -m scantools.run_spot_to_capture \
    --input_path /data/input_dir \
    --output_path /data/output_dir \
    --overwrite \

echo "Done, run_spot_to_capture.py process completed on $LOCATION."