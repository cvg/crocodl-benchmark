#!/bin/bash

SCENE="HYDRO"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/"

docker run --rm \
  -v "$CAPTURE_DIR":/data/capture_dir \
  croco:scantools \
  python3 -m scantools.pipeline_sequence \
    --capture_root "$capture_dir"\
    --scene "$SCENE" \
    #--skip_hololens \
    #--skip_spot \
    #--skip_phone \
    #--run_lamar_splitting

echo "Done, pipeline_sequence process completed!"


