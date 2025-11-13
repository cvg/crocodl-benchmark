#!/usr/bin/env bash
set -euo pipefail

# ==== Config ====
CERES_VERSION="${CERES_VERSION:-2.1.0}"           # Có thể override: CERES_VERSION=2.2.0
CERES_BACKEND="${CERES_BACKEND:-eigen}"           # eigen | suitesparse
USE_SUDO="${USE_SUDO:-sudo}"                      # đổi thành "" nếu không có sudo

# ==== Paths ====
root_folder="$(realpath "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/..")"
source "${root_folder}/scripts/load_env.sh" || true

ext_dir="${root_folder}/external"
ceres_src="${ext_dir}/ceres-solver-v${CERES_VERSION}"

# ==== Prep ====
mkdir -p "${ext_dir}"
cd "${ext_dir}"
${USE_SUDO} rm -rf "${ceres_src}"

# ==== Packages ====
if command -v apt-get >/dev/null 2>&1; then
  ${USE_SUDO} apt-get update -y
  # Gói chung
  ${USE_SUDO} apt-get install -y --no-install-recommends --no-install-suggests \
      cmake libgoogle-glog-dev libgflags-dev libatlas-base-dev libeigen3-dev \
      build-essential

  if [[ "${CERES_BACKEND}" == "suitesparse" ]]; then
    # Đủ deps để CMake tạo đúng imported targets cho SuiteSparse/CXSparse
    ${USE_SUDO} apt-get install -y --no-install-recommends --no-install-suggests \
        libsuitesparse-dev libmetis-dev libtbb-dev
  fi
fi

# ==== Clone ====
git clone -b "${CERES_VERSION}" https://github.com/ceres-solver/ceres-solver.git "ceres-solver-v${CERES_VERSION}" --depth=1
cd "${ceres_src}"

# ==== CMake flags theo backend ====
COMMON_FLAGS=(
  -DCMAKE_BUILD_TYPE=Release
  -DBUILD_TESTING=OFF
  -DBUILD_EXAMPLES=OFF
)

if [[ "${CERES_BACKEND}" == "suitesparse" ]]; then
  # Đầy đủ backend: SuiteSparse + (có thể) CXSparse + EigenSparse
  # Nếu vẫn lỗi CXSparse target, chuyển -DCXSPARSE=OFF
  CMAKE_FLAGS=(
    "${COMMON_FLAGS[@]}"
    -DSUITESPARSE=ON
    -DCXSPARSE=ON
    -DEIGENSPARSE=ON
  )
else
  # Nhanh & chắc: chỉ dùng EigenSparse, tắt hẳn SuiteSparse/CXSparse
  CMAKE_FLAGS=(
    "${COMMON_FLAGS[@]}"
    -DSUITESPARSE=OFF
    -DCXSPARSE=OFF
    -DEIGENSPARSE=ON
  )
fi

# ==== Configure & Build ====
rm -rf build
cmake -S . -B build "${CMAKE_FLAGS[@]}"
cmake --build build --target install -- -j"$(nproc)"

# ==== Post info ====
echo "----------------------------------------"
echo "Ceres ${CERES_VERSION} installed with backend: ${CERES_BACKEND}"
echo "Build dir: ${ceres_src}/build"
