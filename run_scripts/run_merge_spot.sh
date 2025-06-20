#!/bin/bash

NUC_PATH="/home/plukovic/research_assistant/capture/HYDRO/raw/spot/nuc"
ORIN_PATH="/home/plukovic/research_assistant/capture/HYDRO/raw/spot/orin"
OUTPUT_PATH="/home/plukovic/research_assistant/capture/HYDRO/raw/spot/merged"
INPUT_FILE="/home/plukovic/research_assistant/capture/HYDRO/raw/spot/spot_sessions_to_merge.txt"
SCENE="HYDRO"

mkdir -p "$OUTPUT_PATH"

echo "Running merge script on $INPUT_FILE ..."

python3 -m scantools.run_merge_bagfiles \
            --input_file $INPUT_FILE \
            --output_path $OUTPUT_PATH \
            --nuc_path $NUC_PATH \
            --orin_path $ORIN_PATH \
            --scene $SCENE

echo "Merge complete!"
