#!/bin/bash

# Flags and arguments:
# --input_file : path to the input pairs file
# --output_path : path to same merged bagfiles
# --nuc_path : path to the directory storing nuc bagfiles
# --orin_path : path to the directory storing orin bagfiles
# --scene : name of the scene, all capital leters

NUC_DIR="/home/plukovic/research_assistant/capture/HYDRO/raw/spot/nuc"
ORIN_DIR="/home/plukovic/research_assistant/capture/HYDRO/raw/spot/orin"
OUTPUT_DIR="/home/plukovic/research_assistant/capture/HYDRO/raw/spot/merged"
INPUT_FILE="/home/plukovic/research_assistant/capture/HYDRO/raw/spot/spot_sessions_to_merge.txt"
location="HYDRO"

mkdir -p "$OUTPUT_PATH"

echo "Running run_merge_bagfiles on $location inside a Docker ..."

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
    --scene "$location"

echo "Done, run_merge_bagfiles process complete on $location."