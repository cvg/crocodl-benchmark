#!/bin/bash

SCENE="HYDRO"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/"

python3 -m pipelines.pipeline_sequence \
    --capture_root "$CAPTURE_DIR"\
    --scene "$SCENE" \
    #--skip_hololens \
    #--skip_spot \
    #--skip_phone \
    #--run_lamar_splitting
