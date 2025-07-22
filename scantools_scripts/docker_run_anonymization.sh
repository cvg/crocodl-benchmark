#!/bin/bash

# Flags and arguments:
# --capture_path : path capture directory
# --session_id : name of the session to anonymize, if not set, anonymization is done on whole capture folder
# --apikey : apikey for BrighterAI
# --sequential : work on images sequentially, supported only for BrighterAI
# --inplace : save images inplace, otherwise they will be saved in a separate {location}/anonymization_{method} folder
# --overwrite : overwrite existing anonymization folder, only works if inplace flag is NOT set

if [ -z "$CAPTURE_DIR" ]; then
  echo "[ERROR] CAPTURE_DIR env var not set. Make sure to export CAPTURE_DIR=/path/to/data/root."
  exit 1
fi

if [ -z "$LOCATION" ]; then
  echo "[ERROR] LOCATION env var not set. Make sure to export LOCATION=location."
  exit 1
fi

CAPTURE="${CAPTURE_DIR}/${LOCATION}"

echo "You are running with parameters: "
echo "  Capture: ${CAPTURE}"

read -p "Do you want to continue? (y/n): " answer

if [[ ! "$answer" =~ ^[Yy]$ ]]; then
    echo "Execution aborted."
    exit 1
fi

echo "Running run_image_anonymization on $LOCATION inside a Docker ..."

docker run --rm \
  -v "$CAPTURE":/data/capture_dir \
  croco:scantools \
  python3 -m scantools.run_image_anonymization \
    --capture_path /data/capture_dir \
    #--session_id "spot_2023-12-08-11-13" \
    #--apikey "apikey" \
    #--sequential \
    #--inplace \

echo "Done, run_image_anonymization completed on $LOCATION."