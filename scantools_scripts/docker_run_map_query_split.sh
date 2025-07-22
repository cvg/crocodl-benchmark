#!/bin/bash

# Flags and arguments:
# --capture_path : path to capture directory
# --{device}{m/q} : generate {m/q} for the {device}
# --transform : generate 4DOF transformation and transform trajectories
# --just_vis : only generate visualizations and files, without overwriting

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

echo "Running run_map_query_split_manual on $LOCATION inside a Docker ..."

docker run --rm \
  -v "$CAPTURE":/data/input_dir \
  croco:scantools \
  python3 -m scantools.run_map_query_split_manual \
      --capture_path /data/input_dir \
      --iosm --iosq --hlq --hlm --spotq --spotm \
      --transform \
      #--just_vis

echo "Done, run_map_query_split_manual process completed on $LOCATION."
