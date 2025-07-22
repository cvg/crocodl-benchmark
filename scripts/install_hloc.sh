#!/usr/bin/env bash

root_folder=$(realpath $(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/..)
source ${root_folder}/scripts/load_env.sh

mkdir -p ${root_folder}/external
cd ${root_folder}/external
rm -rf ${root_folder}/external/hloc

git clone --recursive -b crocodl/v1.4 https://github.com/PetarLukovic/Hierarchical-Localization.git hloc --depth=1
cd ${root_folder}/external/hloc

python -m pip install -e .