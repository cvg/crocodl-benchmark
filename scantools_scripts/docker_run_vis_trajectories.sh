#!/usr/bin/env bash

# Flags and arguments:
# --capture_path : path to capture directory
# --{device} : flags that need to be set to visualize map query split for specific device

if [ -z "$CAPTURE_DIR" ]; then
  echo "[ERROR] CAPTURE_DIR env var not set. Make sure to export CAPTURE_DIR=/path/to/data/root."
  exit 1
fi

if [ -z "$LOCATION" ]; then
  echo "[ERROR] LOCATION env var not set. Make sure to export LOCATION=location."
  exit 1
fi

CAPTURE="${CAPTURE_DIR}/${LOCATION}"

echo "You are running with parameters: "
echo "  Capture: ${CAPTURE}"

read -p "Do you want to continue? (y/n): " answer

if [[ ! "$answer" =~ ^[Yy]$ ]]; then
    echo "Execution aborted."
    exit 1
fi

echo "Running run_visualize_trajectories on location $LOCATION inside a Docker ..."

docker run --rm \
  -v "$CAPTURE":/data/capture_dir \
  croco:scantools \
  python3 -m scantools.run_visualize_trajectories \
    --capture_path /data/capture_dir  \
    --ios --spot --hl

echo "Done, run_visualize_trajectories process completed on $LOCATION."