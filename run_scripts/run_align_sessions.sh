#!/bin/bash

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
