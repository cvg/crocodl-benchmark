#!/usr/bin/env bash
set -euo pipefail

root_folder="$(realpath "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/..")"
source "${root_folder}/scripts/load_env.sh" || true

ext_dir="${root_folder}/external"

mkdir -p "${ext_dir}"

# đảm bảo thư mục thuộc về user hiện tại
if [ ! -w "${ext_dir}" ]; then
  echo "[info] Fixing permissions on ${ext_dir}"
  sudo chown -R "$USER":"$USER" "${ext_dir}"
  chmod -R u+rwX,go-w "${ext_dir}"
fi

cd "${ext_dir}"
rm -rf "${ext_dir}/hloc"

git clone --recursive -b crocodl/v1.4 \
  https://github.com/PetarLukovic/Hierarchical-Localization.git hloc --depth=1

cd "${root_folder}/external/hloc"
python3 -m pip install -e .
