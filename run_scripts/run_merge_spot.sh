#!/bin/bash

# Flags and arguments:
# --input_file : path to the input pairs file
# --output_path : path to same merged bagfiles
# --nuc_path : path to the directory storing nuc bagfiles
# --orin_path : path to the directory storing orin bagfiles
# --scene : name of the scene, all capital leters

NUC_PATH="/home/plukovic/research_assistant/capture/HYDRO/raw/spot/nuc"
ORIN_PATH="/home/plukovic/research_assistant/capture/HYDRO/raw/spot/orin"
OUTPUT_PATH="/home/plukovic/research_assistant/capture/HYDRO/raw/spot/merged"
INPUT_FILE="/home/plukovic/research_assistant/capture/HYDRO/raw/spot/spot_sessions_to_merge.txt"
location="HYDRO"

mkdir -p "$OUTPUT_PATH"

echo "Running run_merge_bagfiles on $location ..."

python3 -m scantools.run_merge_bagfiles \
            --input_file $INPUT_FILE \
            --output_path $OUTPUT_PATH \
            --nuc_path $NUC_PATH \
            --orin_path $ORIN_PATH \
            --scene $SCENE

echo "Done, run_merge_bagfiles process completed on $location."
