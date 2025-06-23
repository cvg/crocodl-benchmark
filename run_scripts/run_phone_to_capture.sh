#!/usr/bin/env bash

location="HYDRO"
INPUT_PATH="/home/plukovic/research_assistant/capture/HYDRO/raw/phone"
CAPTURE_PATH="/home/plukovic/research_assistant/capture/${location}/"

echo "Running run_phone_to_capture on $location ..."

python3 -m scantools.run_phone_to_capture \
    --input_path $INPUT_PATH \
    --capture_path $CAPTURE_PATH \
    #--visualize 

echo "Done, run_phone_to_capture process completed on $location."
