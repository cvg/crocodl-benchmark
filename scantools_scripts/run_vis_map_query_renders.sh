#!/usr/bin/env bash

# Flags and arguments:
# --capture_path : path to the capture directory
# --skip : this is the subsampling rate of the rendering
# --num_workers : number of processing cores used for rendering
# --save_video : save rendering comparisons in form of a video
# --simplified_mesh : use simplified mesh (uses less RAM)

# Consider using --simplified_mesh flag if you have less that 32GB RAM. Most of the locations 
# would not run with less than 32GB RAM.

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

echo "Running run_visualize_map_query_renders on $LOCATION ..."

python3 -m scantools.run_visualize_map_query_renders \
  --capture_path "$CAPTURE" \
  --skip "10" \
  --num_workers 2 \
  --save_video \
  --simplified_mesh \

echo "Done, run_visualize_map_query_renders process completed for $LOCATION."
