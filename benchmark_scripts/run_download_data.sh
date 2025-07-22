#!/bin/bash

# Flags and arguments:
# --capture_dir : path capture directory (exported via CAPTURE_DIR)
# --challenge_data : download challenge data
# --full_data : download full release data
# --raw_data : download raw data

# --- Check environment variable ---
if [ -z "$CAPTURE_DIR" ]; then
  echo "[ERROR] CAPTURE_DIR env var not set. Make sure to export CAPTURE_DIR=/path/to/data/root."
  exit 1
fi

# --- Parse flags ---
CHALLENGE=false
FULL_RELEASE=false
RAW=false

for arg in "$@"; do
  [[ $arg == --challenge_data ]] && CHALLENGE=true && echo "Flag detected: --challenge_data"
  [[ $arg == --full_data ]] && FULL_RELEASE=true && echo "Flag detected: --full_data"
  [[ $arg == --raw_data ]] && RAW=true && echo "Flag detected: --raw_data"
done

if ! $CHALLENGE && ! $FULL_RELEASE && ! $RAW; then
  echo "[ERROR] You must provide at least one flag: --challenge_data, --full_data or --raw_data"
  exit 1
fi

# --- Define scenes ---
CHALLENGE_SCENES=("HYDRO", "SUCCULENT")
FULL_RELEASE_SCENES=("ARCHE_D2")
RAW_SCENES=("ARCHE_D2")
MAX_WORKERS=16

echo "You are running with parameters: "
echo "  Capture: ${CAPTURE_DIR}"
echo "  Max workers: ${MAX_WORKERS}"
echo "  Challenge data: ${CHALLENGE}"
echo "    Challenge scenes: ${CHALLENGE_SCENES[@]}"
echo "  Full release data: ${FULL_RELEASE}"
echo "    Full release scenes: ${FULL_RELEASE_SCENES[@]}"
echo "  Raw data: ${RAW}"
echo "    Raw scenes: ${RAW_SCENES[@]}"
echo "  Codabench folder: ${CAPTURE_DIR}/codabench"

read -p "Do you want to continue? (y/n): " answer
if [[ ! "$answer" =~ ^[Yy]$ ]]; then
    echo "Execution aborted."
    exit 1
fi

# --- Create capture directory ---
echo "Creating capture directory: ${CAPTURE_DIR}"
mkdir -p "${CAPTURE_DIR}"

# --- Challenge scenes ---
if $CHALLENGE; then
  echo "Running in challenge mode ..."
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

  for scene in "${CHALLENGE_SCENES[@]}"; do
    scene_challenge="${scene}-challenge-test"
    target_dir="${CAPTURE_DIR}/${scene}"

    if [[ -d "$target_dir" ]]; then
      echo "Scene $scene already exists, skipping download."
    else    
      mkdir -p "${target_dir}/sessions"
      cd "$target_dir" || { echo "Failed to cd to $target_dir"; exit 1; }
      hf download "CroCoDL/${scene_challenge}" --repo-type dataset --local-dir "${target_dir}/sessions" --max-workers "${MAX_WORKERS}"
      rm -rf "${target_dir}/sessions/.gitattributes"

      # --- Unzip all .zip files and delete them ---
      echo "Unzipping .zip files in $target_dir ..."
      find "$target_dir" -type f -name "*.zip" | while read zipfile; do
        unzip -o "$zipfile" -d "$(dirname "$zipfile")"
        if [[ $? -eq 0 ]]; then
          rm "$zipfile"
          echo "Unzipped and removed $zipfile"
        else
          echo "[WARNING] Failed to unzip $zipfile"
        fi
      done
    fi

  done

  echo "Done downloading challenge data."
fi

# --- Full release scenes ---
if $FULL_RELEASE; then
  echo "Downloading full release scenes ..."

  for scene in "${FULL_RELEASE_SCENES[@]}"; do
    target_dir="${CAPTURE_DIR}/${scene}"

    if [[ -d "$target_dir/sessions" ]]; then
      echo "Scene $scene/sessions already exists, skipping download."
    else
      echo "Downloading full release scene $scene ..."
      hf download "CroCoDL/${scene}" --repo-type dataset --local-dir "${target_dir}" --max-workers "${MAX_WORKERS}"

      if [[ $? -ne 0 ]]; then
          echo "[ERROR] Failed to download $scene"
          exit 1
      fi

      rm -rf "${target_dir}/.gitattributes"

      echo "Downloaded release data for $scene."

      # Move specific files to capture root if they exist
      for file in "${scene}_hololens.txt" "${scene}_phone.txt" "${scene}_spot.txt"; do
        [[ -f "$target_dir/$file" ]] && mv "$target_dir/$file" "$CAPTURE_DIR"
      done

      # --- Unzip all .zip files and delete them ---
      echo "Unzipping .zip files in $target_dir ..."
      find "$target_dir" -type f -name "*.zip" | while read zipfile; do
        unzip -o "$zipfile" -d "$(dirname "$zipfile")"
        if [[ $? -eq 0 ]]; then
          rm "$zipfile"
          echo "Unzipped and removed $zipfile"
        else
          echo "[WARNING] Failed to unzip $zipfile"
        fi
      done
      
    fi

  done

  echo "Full release data done."
fi

# --- Raw scenes ---
if $RAW; then
  echo "Downloading raw scenes ..."

  for scene in "${RAW_SCENES[@]}"; do
    target_dir="${CAPTURE_DIR}/${scene}"
    scene_raw="${scene}-raw"

    if [[ -d "$target_dir/raw" ]]; then
      echo "Scene $scene/raw already exists, skipping download."
    else
      echo "Downloading raw scene $scene ..."
      hf download "CroCoDL/${scene_raw}" --repo-type dataset --local-dir "${target_dir}" --max-workers "${MAX_WORKERS}"

      if [[ $? -ne 0 ]]; then
          echo "[ERROR] Failed to download $scene"
          exit 1
      fi

      rm -rf "${target_dir}/.gitattributes"

      echo "Downloaded raw for $scene."

      # --- Unzip all .zip files and delete them ---
      echo "Unzipping .zip files in $target_dir ..."
      find "$target_dir" -type f -name "*.zip" | while read zipfile; do
        unzip -o "$zipfile" -d "$(dirname "$zipfile")"
        if [[ $? -eq 0 ]]; then
          rm "$zipfile"
          echo "Unzipped and removed $zipfile"
        else
          echo "[WARNING] Failed to unzip $zipfile"
        fi
      done
      
    fi

  done

  echo "Full release data done."
fi



