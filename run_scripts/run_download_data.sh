#!/bin/bash

# Flags and arguments:
# --capture_dir : path capture directory
# --challenge : download challenge data
# --full_release : download full release data

# Alternate capture_dir to change download location

CAPTURE_DIR="/home/plukovic/research_assistant/capture"

CHALLENGE=false; FULL_RELEASE=false
for arg in "$@"; do
  [[ $arg == --challenge ]] && CHALLENGE=true && echo "Flag detected: --challenge"
  [[ $arg == --full_release ]] && FULL_RELEASE=true && echo "Flag detected: --full_release"
done

if ! $CHALLENGE && ! $FULL_RELEASE; then
  echo "Error: You must provide at least one flag: --challenge or --full_release"
  exit 1
fi

mkidr -p "${CAPTURE_DIR}"

if $CHALLENGE; then
  echo "Running in challenge mode..."
  scenes=("HYDRO" "SUCCULENT")
  for scene in "${scenes[@]}"; do
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
  # Add your full release logic here
fi
