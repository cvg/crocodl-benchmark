#!/usr/bin/env bash

location="HYDRO"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"

python -m scantools.run_map_query_split_manual \
      --capture_path "$CAPTURE_DIR" \
      --iosm --iosq --hlq --hlm --spotq --spotm
  
