#!/usr/bin/env bash

location="HYDRO"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"

echo "Running run_query_pruning on $location ..."

python -m scantools.run_query_pruning \
      --capture_path "$CAPTURE_DIR" 
  
echo "Done, run_query_pruning process completed on $location."
