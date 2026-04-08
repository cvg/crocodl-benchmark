#!/usr/bin/env bash

root_folder=$(realpath $(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/..)
source ${root_folder}/scripts/load_env.sh

mkdir -p ${root_folder}/external
cd ${root_folder}/external
rm -rf ${root_folder}/external/hloc

git clone --recursive -b crocodl/v1.4 https://github.com/PetarLukovic/Hierarchical-Localization.git hloc --depth=1
cd ${root_folder}/external/hloc

python -m pip install -e .

# ensure curope is installed
cd ${root_folder}/external/hloc/third_party/mast3r/dust3r/croco/models/curope
python setup.py build_ext --inplace