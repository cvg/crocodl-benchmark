#!/bin/bash

# Flags and arguments:
# --capture_path : path capture directory
# --session_id : name of the session to anonymize, if not set, anonymization is done on whole capture folder
# --apikey : apikey for BrighterAI
# --sequential : work on images sequentially, supported only for BrighterAI
# --inplace : save images inplace, otherwise they will be saved in a separate {location}/anonymization_{method} folder
# --overwrite : overwrite existing anonymization folder, only works if inplace flag is NOT set

location="DESIGN"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}"

echo "Running run_image_anonymization on $location ..."

python3 -m scantools.run_image_anonymization \
    --capture_path "$CAPTURE_DIR" \
    #--session_id "spot_2023-12-08-11-13" \
    #--apikey "apikey" \
    #--sequential \
    #--inplace \
    #--overwrite \

echo "Done, run_image_anonymization completed on $location."