#!/bin/bash

# Flags and arguments:
# --file_path : path to benchmarking ouput file
# --conf_matrix : calculate and print confusion matrices

# Please sanity check output of this script! 
# Script only works if you run it on output of full data release. Challenge data does not have ground
# truth, so recalls would not be printed out.

OUTPUT_FILE="$1"

if [ -z "$OUTPUT_FILE" ]; then
  echo "Usage: $0 path/to/output_file.txt"
  exit 1
fi

echo "You are running with parameters: "
echo "  Output: ${OUTPUT_FILE}"

read -p "Do you want to continue? (y/n): " answer

if [[ ! "$answer" =~ ^[Yy]$ ]]; then
    echo "Execution aborted."
    exit 1
fi


echo "Running read_benchmarking_output on $OUTPUT_FILE inside a Docker ..."

docker run --rm \
      -v "$OUTPUT_FILE":/data/output_file.txt \
      croco:lamar \
      python -m lamar.read_benchmarking_output \
            --file_path /data/output_file.txt \
            --conf_matrix

echo "Done, read_benchmarking_output process completed on $OUTPUT_FILE."