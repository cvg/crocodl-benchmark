#!/bin/bash

# Flags and arguments:
# --capture_dir : path capture directory
# --challenge : download challenge data
# --full_release : download full release data
# --challenge_scenes : list of challenge scenes to download
# --full_release_scenes : list of full release scenes to download
# --arche : download arche data
# --arche_scenes : list of arche scenes to download

set -euo pipefail

if [ -z "$CAPTURE_DIR" ]; then
  echo "[ERROR] CAPTURE_DIR env var not set. Make sure to export CAPTURE_DIR=/path/to/data/root."
  exit 1
fi

CHALLENGE=false; FULL_RELEASE=false; ARCHE=false
for arg in "$@"; do
  [[ $arg == --challenge ]] && CHALLENGE=true && echo "Flag detected: --challenge"
  [[ $arg == --full_release ]] && FULL_RELEASE=true && echo "Flag detected: --full_release"
  [[ $arg == --arche ]] && ARCHE=true && echo "Flag detected: --arche"
done

if ! $CHALLENGE && ! $FULL_RELEASE && ! $ARCHE; then
  echo "Error: You must provide at least one flag: --challenge or --full_release or --arche"
  exit 1
fi

CHALLENGE_SCENES=("HYDRO" "SUCCULENT")
FULL_RELEASE_SCENES=("TBD")
ARCHE_SCENES=("ARCHE_D2") 
ARCHE_PATTERNS=("sessions/**") # (sessions) or ("sessions/*_map" "sessions/*_query") or (...)

echo "You are running with parameters: "
echo "  Capture: ${CAPTURE_DIR}"
echo "  Challenge data: ${CHALLENGE}"
echo "    Challenge scenes: ${CHALLENGE_SCENES[@]}"
echo "  Full release data: ${FULL_RELEASE}"
echo "    Full release scenes: ${FULL_RELEASE_SCENES[@]}"
echo "  Arche data: ${ARCHE}"
echo "    Arche scenes: ${ARCHE_SCENES[@]}"
echo "    Arche patterns: ${ARCHE_PATTERNS[@]}"
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
Code Link: link/to/your/code;
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
    git clone "https://hf.co/datasets/CroCoDL/$hf_dataset.git"
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

#######################################################################################


#############################
if [ "$ARCHE" ]; then
  echo "[INFO] Running in ARCHE mode..."

  # 1. Check that huggingface_hub is installed
  if ! python3 -c "import huggingface_hub" >/dev/null 2>&1; then
    echo "[INFO] Installing huggingface_hub..."
    pip install -q huggingface_hub hf_transfer || {
      echo "[ERROR] Failed to install huggingface_hub"
      exit 1
    }
  fi
  export HF_HUB_ENABLE_HF_TRANSFER=1

  # 2. Loop through all scenes
  for scene in "${ARCHE_SCENES[@]}"; do
    echo "[INFO] Downloading scene: ${scene}"
    target_dir="${CAPTURE_DIR}/${scene}"

    # python3 -m benchmark_scripts.hf_download \
    #   --repo_id "CroCoDL/${scene}" \
    #   --allow_patterns "sessions" \
    #   --local_dir "${target_dir}" \

    hf download \
      "CroCoDL/${scene}" \
      --repo-type dataset \
      --include "${ARCHE_PATTERNS[@]}" \
      --local-dir "${target_dir}" \
      --force-download

    if [ $? -ne 0 ]; then
      echo "[WARNING] Download failed for scene: ${scene}"
    fi
  done

  echo "[INFO] Done downloading challenge data."
fi