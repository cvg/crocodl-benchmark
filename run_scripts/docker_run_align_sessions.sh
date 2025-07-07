#!/bin/bash

# Flags and arguments:
# --capture_root : path to capture directory (without the scene name)
# --scene : name of the scene, all capital leters
# --skip_{device} : skips alignment of the device indicated with {device}
# --run_lamar_splitting : runs lamar automatic map/query split (we recommend skipping this argument)

location="HYDRO"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/"

echo "Running pipeline_sequence on $location inside a Docker ..."

docker run --rm \
  -v "$CAPTURE_DIR":/data/capture_dir \
  croco:scantools \
  python3 -m scantools.pipeline_sequence \
    --capture_root /data/capture_dir \
    --scene "$location" \
    #--skip_hololens \
    #--skip_spot \
    #--skip_phone \
    #--run_lamar_splitting

echo "Done, pipeline_sequence process completed on $location."


