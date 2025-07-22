#!/usr/bin/env bash

# Flags and arguments:
# --capture_path : path to the capture directory
# --just_vis : only generates visuals

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

echo "Running run_query_pruning on $LOCATION ..."

python -m scantools.run_query_pruning \
      --capture_path "$CAPTURE" \
      #--just_vis
  
echo "Done, run_query_pruning process completed on $LOCATION."
