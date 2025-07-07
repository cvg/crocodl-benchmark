#!/usr/bin/env bash

# Flags and arguments:
# --capture_path : path to capture directory

# This script will run matrix visualization on all combinations of given devices.
# You can tune it to your liking, or just run it once with wanted flags.

location="HYDRO"
CAPTURE_DIR="/home/plukovic/research_assistant/capture/${location}/"

flags=(--ios --spot --hl)

echo "Running run_visualize_map_query_matrix with all combinations of 2 and 3 flags on location {$location} inside a Docker ..."

# All 2-combinations
for ((i=0; i<${#flags[@]}-1; i++)); do
  for ((j=i+1; j<${#flags[@]}; j++)); do
    echo "Running run_visualize_map_query_matrix with flags: ${flags[i]} ${flags[j]} ..."
    docker run --rm \
      -v "$CAPTURE_DIR":/data/capture_dir \
      croco:scantools \
      python3 -m scantools.run_visualize_map_query_matrix \
        --capture_path /data/capture_dir \
        "${flags[i]}" "${flags[j]}"
    echo "Done, run_visualize_map_query_matrix process completed with flags: ${flags[i]} ${flags[j]}."
  done
done

# 3-combination
echo "Running run_visualize_map_query_matrix with flags: ${flags[*]} ..."
docker run --rm \
  -v "$CAPTURE_DIR":/data/capture_dir \
  croco:scantools \
  python3 -m scantools.run_visualize_map_query_matrix \
    --capture_path /data/capture_dir \
    "${flags[@]}"
echo "Done, run_visualize_map_query_matrix process completed with flags: ${flags[*]}."

echo "Done, run_visualize_map_query_matrix with all combinations of 2 and 3 flags on $location."