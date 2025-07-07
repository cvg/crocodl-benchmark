#!/bin/bash

# Flags and arguments:
# --capture_root : path to capture directory (without the scene name)
# --scene : name of the scene, all capital leters
# --skip_{device} : skips alignment of the device indicated with {device}
# --run_lamar_splitting : runs lamar automatic map/query split (we recommend skipping this argument)

location="HYDRO"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/"

echo "Running pipeline_sequence on $location ..."

python3 -m pipelines.pipeline_sequence \
    --capture_root "$CAPTURE_DIR"\
    --scene "$location" \
    #--skip_hololens \
    #--skip_spot \
    #--skip_phone \
    #--run_lamar_splitting

echo "Done, pipeline_sequence completed on $location."
