#!/bin/bash

# Flags and arguments:
# --file_path : path to benchmarking ouput file
# --conf_matrix : calculate and print confusion matrices

# Please sanity check output of this script!

OUTPUT_FILE="/home/plukovic/research_assistant/crocodl-benchmark/b3.txt"

echo "Running run_read_benchmarking_output on $OUTPUT_FILE ..."

python -m lamar.run_read_benchmarking_output \
      --file_path "$OUTPUT_FILE" \
      --conf_matrix
  
echo "Done, run_read_benchmarking_output process completed on $OUTPUT_FILE."