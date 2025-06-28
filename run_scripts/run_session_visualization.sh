#!/usr/bin/env bash

location="HYDRO"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"
QUERY_ID="spot_2023-11-24-11-13"
REF_ID="2023-11-03_10.31.58+2023-11-03_13.51.06"

echo "Running run_sequence_rerendering on $location ..."

python3 -m scantools.run_sequence_rerendering \
  --capture_path "$CAPTURE_DIR" \
  --query_id "$QUERY_ID" \
  --ref_id "$REF_ID"

echo "Done, run_sequence_rerendering process completed for $location."