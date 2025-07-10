#!/bin/bash

# Flags and arguments:
# --file_path : path to benchmarking ouput file
# --conf_matrix : calculate and print confusion matrices

# Please sanity check output of this script!

OUTPUT_FILE="/home/plukovic/research_assistant/crocodl-benchmark/ag.txt"

echo "Running run_read_benchmarking_output on $OUTPUT_FILE inside a Docker ..."

docker run --rm \
      -v "$OUTPUT_FILE":/data/output_file.txt \
      croco:lamar \
      python -m lamar.run_read_benchmarking_output \
            --file_path /data/output_file.txt \
            --conf_matrix

echo "Done, run_read_benchmarking_output process completed on $OUTPUT_FILE."