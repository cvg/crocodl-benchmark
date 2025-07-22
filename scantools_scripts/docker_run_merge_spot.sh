#!/bin/bash

# Flags and arguments:
# --input_file : path to the input pairs file
# --output_path : path to same merged bagfiles
# --nuc_path : path to the directory storing nuc bagfiles
# --orin_path : path to the directory storing orin bagfiles
# --scene : name of the scene, all capital leters

if [ -z "$CAPTURE_DIR" ]; then
  echo "[ERROR] CAPTURE_DIR env var not set. Make sure to export CAPTURE_DIR=/path/to/data/root."
  exit 1
fi

if [ -z "$LOCATION" ]; then
  echo "[ERROR] LOCATION env var not set. Make sure to export LOCATION=location."
  exit 1
fi

CAPTURE="${CAPTURE_DIR}/${LOCATION}"
NUC_PATH="${CAPTURE}/raw/spot/nuc"
ORIN_PATH="${CAPTURE}/raw/spot/orin"
OUTPUT_PATH="${CAPTURE}/raw/spot/merged"
INPUT_FILE="${CAPTURE}/raw/spot/spot_sessions_to_merge.txt"

echo "You are running with parameters: "
echo "  Capture: ${CAPTURE}"
echo "  Nuc path: ${NUC_PATH}"
echo "  Orin path: ${ORIN_PATH}"
echo "  Output path: ${OUTPUT_PATH}"
echo "  Input file: ${INPUT_FILE}"

read -p "Do you want to continue? (y/n): " answer

if [[ ! "$answer" =~ ^[Yy]$ ]]; then
    echo "Execution aborted."
    exit 1
fi

echo "Running run_merge_bagfiles on $LOCATION inside a Docker ..."

docker run --rm \
  -v "$NUC_DIR":/data/nuc_dir \
  -v "$ORIN_DIR":/data/orin_dir \
  -v "$OUTPUT_DIR":/data/merged_dir \
  -v "$INPUT_FILE":/data/input.txt \
  croco:scantools \
  python3 -m scantools.run_merge_bagfiles \
    --input_file /data/input.txt \
    --output_path /data/merged_dir \
    --nuc_path /data/nuc_dir \
    --orin_path /data/orin_dir \
    --scene "$LOCATION"

echo "Done, run_merge_bagfiles process complete on $LOCATION."