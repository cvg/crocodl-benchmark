#!/bin/bash

# Visualization script for cross-device pose estimation results
# Supports multiple query-map pairs with color differentiation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

if [ -z "$CAPTURE_DIR" ]; then
  echo "[ERROR] CAPTURE_DIR env var not set."
  exit 1
fi

# Configuration
BENCHMARKING_DIR="long/benchmarking_results"
LOCAL_FEATURE_METHOD="superpoint"
MATCHING_METHOD="lightglue"
GLOBAL_FEATURE_METHOD="megaloc"
LOCATION="arche_d2"
QUERY_DEVICES="ios"     # or "ios hl spot"
MAP_DEVICES="ios"       # or "ios hl spot"
SCALE=0.1
MAX_POSES=""
PYTHON_SCRIPT="${SCRIPT_DIR}/cam_pose_visualizer.py"

if [[ ! -d "$CAPTURE_DIR" ]]; then
    echo "Error: CAPTURE_DIR not found: $CAPTURE_DIR"
    exit 1
fi

python3 -c "import open3d, numpy, scipy; print('Dependencies OK')" 2>/dev/null || {
    echo "Error: Install open3d numpy scipy"
    exit 1
}

LOCATION_PATH="${LOCATION^^}"
[ "$LOCATION" = "succu" ] && LOCATION_PATH="SUCCULENT"

# Build arguments for all device pairs
POSE_ARGS=""
for query in $QUERY_DEVICES; do
    for map in $MAP_DEVICES; do
        GT_POSES="${CAPTURE_DIR}/${LOCATION_PATH}/sessions/${query}_query/proc/alignment_trajectories.txt"
        SENSORS="${CAPTURE_DIR}/${LOCATION_PATH}/sessions/${query}_query/sensors.txt"
        RIGS="${CAPTURE_DIR}/${LOCATION_PATH}/sessions/${query}_query/rigs.txt"
        
        DEVICE_TYPE="single_image"
        [ "$query" != "ios" ] && DEVICE_TYPE="rig"
        
        EST_POSES="${CAPTURE_DIR}/${LOCATION_PATH}/${BENCHMARKING_DIR}/pose_estimation/${query}_query/${map}_map/${LOCAL_FEATURE_METHOD}/${MATCHING_METHOD}/${GLOBAL_FEATURE_METHOD}/triangulation/${DEVICE_TYPE}/poses.txt"
        
        if [[ ! -f "$GT_POSES" ]] || [[ ! -f "$EST_POSES" ]]; then
            echo "Warning: Skipping ${query}->${map} (files not found)"
            continue
        fi
        
        POSE_ARGS="$POSE_ARGS --pair $query $map \"$GT_POSES\" \"$EST_POSES\" \"$SENSORS\""
        [ -f "$RIGS" ] && POSE_ARGS="$POSE_ARGS \"$RIGS\"" || POSE_ARGS="$POSE_ARGS \"\""
    done
done

if [ -z "$POSE_ARGS" ]; then
    echo "Error: No valid device pairs found"
    exit 1
fi

CMD="python3 ${PYTHON_SCRIPT} --scale ${SCALE}"
[ -n "$MAX_POSES" ] && CMD="$CMD --max_poses ${MAX_POSES}"
CMD="$CMD $POSE_ARGS"

echo "Visualizing: Location=${LOCATION}, Query=${QUERY_DEVICES}, Map=${MAP_DEVICES}"
eval $CMD
