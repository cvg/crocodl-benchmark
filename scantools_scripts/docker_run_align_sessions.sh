#!/bin/bash

# Flags and arguments:
# --capture_root : path to capture directory (without the scene name)
# --scene : name of the scene, all capital leters
# --skip_{device} : skips alignment of the device indicated with {device}
# --run_lamar_splitting : runs lamar automatic map/query split (we recommend skipping this argument)

if [ -z "$CAPTURE_DIR" ]; then
  echo "[ERROR] CAPTURE_DIR env var not set. Make sure to export CAPTURE_DIR=/path/to/data/root."
  exit 1
fi

if [ -z "$LOCATION" ]; then
  echo "[ERROR] LOCATION env var not set. Make sure to export LOCATION=location."
  exit 1
fi

echo "You are running with parameters: "
echo "  Capture: ${CAPTURE_DIR}"
echo "  Location: ${LOCATION}"

read -p "Do you want to continue? (y/n): " answer

if [[ ! "$answer" =~ ^[Yy]$ ]]; then
    echo "Execution aborted."
    exit 1
fi

echo "Running pipeline_sequence on $LOCATION inside a Docker ..."

docker run --rm \
  -v "$CAPTURE_DIR":/data/capture_dir \
  croco:scantools \
  python3 -m scantools.pipeline_sequence \
    --capture_root /data/capture_dir \
    --scene "$LOCATION" \
    #--skip_hololens \
    #--skip_spot \
    #--skip_phone \
    #--run_lamar_splitting

echo "Done, pipeline_sequence process completed on $LOCATION."


