#!/bin/bash

# Define host-side paths
NUC_PATH="/home/plukovic/research_assistant/capture/HYDRO/raw/spot/nuc"
ORIN_PATH="/home/plukovic/research_assistant/capture/HYDRO/raw/spot/orin"
OUTPUT_PATH="/home/plukovic/research_assistant/capture/HYDRO/raw/spot/merged"
INPUT_FILE="/home/plukovic/research_assistant/capture/HYDRO/raw/spot/spot_sessions_to_merge.txt"
SCENE="HYDRO"

# Ensure output path exists on host
mkdir -p "$OUTPUT_PATH"

echo "Running merge inside Docker..."

docker run --rm \
  -v "$NUC_PATH":/data/nuc_dir \
  -v "$ORIN_PATH":/data/orin_dir \
  -v "$OUTPUT_PATH":/data/merged_dir \
  -v "$INPUT_FILE":/data/input.txt \
  croco:scantools \
  python3 -m scantools.run_merge_bagfiles \
    --input_file /data/input.txt \
    --output_path /data/merged_dir \
    --nuc_path /data/nuc_dir \
    --orin_path /data/orin_dir \
    --scene "$SCENE"

echo "Merge complete!"