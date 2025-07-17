#!/bin/bash

# Flags and arguments:
# --capture_dir : path capture directory
# --challenge : download challenge data
# --full_release : download full release data
# --challenge_scenes : list of challenge scenes to download
# --full_release_scenes : list of full release scenes to download

if [ -z "$CAPTURE_DIR" ]; then
  echo "[ERROR] CAPTURE_DIR env var not set. Make sure to export CAPTURE_DIR=/path/to/data/root."
  exit 1
fi

CHALLENGE=false; FULL_RELEASE=false
for arg in "$@"; do
  [[ $arg == --challenge ]] && CHALLENGE=true && echo "Flag detected: --challenge"
  [[ $arg == --full_release ]] && FULL_RELEASE=true && echo "Flag detected: --full_release"
done

if ! $CHALLENGE && ! $FULL_RELEASE; then
  echo "Error: You must provide at least one flag: --challenge or --full_release"
  exit 1
fi

CHALLENGE_SCENES=("HYDRO" "SUCCULENT")
FULL_RELEASE_SCENES=("TBD")

echo "You are running with parameters: "
echo "  Capture: ${CAPTURE_DIR}"
echo "  Challenge data: ${CHALLENGE}"
echo "    Challenge scenes: ${CHALLENGE_SCENES[@]}"
echo "  Full release data: ${FULL_RELEASE}"
echo "    Full release scenes: ${FULL_RELEASE_SCENES[@]}"
echo "  Codabench folder: ${CAPTURE_DIR}/codabench"

read -p "Do you want to continue? (y/n): " answer

if [[ ! "$answer" =~ ^[Yy]$ ]]; then
    echo "Execution aborted."
    exit 1
fi

echo "Creating capture directory: ${CAPTURE_DIR}"
mkdir -p "${CAPTURE_DIR}/codabench"

echo "Creating model description dummy file: ${CAPTURE_DIR}/codabench/desc.txt"
cat <<EOF > "${CAPTURE_DIR}/codabench/desc.txt"
Retrieval Features: Fusion (NetVLAD, APGeM);
Local Features: SuperPoint;
Feature Matching: LightGlue;
Description:
Default lamar-benchmark parameters for extractors, matchers, and pipeline.
Retrieved top 10 images for both mapping and localization with frustum filtering for mapping.
PnP error multiplier 3 for single-image, 1 for rigs.
EOF

if $CHALLENGE; then
  echo "Running in challenge mode..."
  for scene in "${CHALLENGE_SCENES[@]}"; do
    hf_dataset="${scene}-challenge"
    target_dir="${CAPTURE_DIR}/${scene}"
    rm -rf "${target_dir}"
    mkdir -p "${target_dir}"
    cd "$target_dir" || { echo "Failed to cd to $target_dir"; exit 1; }
    git clone "git@hf.co:datasets/CroCoDL/$hf_dataset.git"
    mv "${target_dir}/${hf_dataset}" "${target_dir}/sessions"
    rm -rf "${target_dir}/sessions/.git"
    rm -rf "${target_dir}/sessions/.gitattributes"
  done
  echo "Done downloading challenge data"
fi

if $FULL_RELEASE; then
  echo "Running in full release mode..."
  # TODO
fi
