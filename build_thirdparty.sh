# iKalibr: Unified Targetless Spatiotemporal Calibration Framework
# Copyright 2024, the School of Geodesy and Geomatics (SGG), Wuhan University, China
# https://github.com/Unsigned-Long/iKalibr.git
#
# Author: Shuolong Chen (shlchen@whu.edu.cn)
# GitHub: https://github.com/Unsigned-Long
#  ORCID: 0000-0002-5283-9057
#
# Purpose: See .h/.hpp file.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * The names of its contributors can not be
#   used to endorse or promote products derived from this software without
#   specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# update submodules
echo "----------------------------------------------------"
echo "update submodules remotely, it may take some time..."
echo "----------------------------------------------------"
git submodule update --init --recursive
if [ $? -ne 0 ]; then
    echo "--------------------------------------------"
    echo "error occurs when updating submodules, exit!"
    echo "--------------------------------------------"
    exit
fi

# shellcheck disable=SC2046
IKALIBR_ROOT_PATH=$(cd $(dirname $0) || exit; pwd)
echo "the root path of 'iKalibr': ${IKALIBR_ROOT_PATH}"

# build tiny-viewer
echo "----------------------------------"
echo "build thirdparty: 'tiny-viewer'..."
echo "----------------------------------"

# Apply patches to fix OpenGL and optional issues without modifying submodule files
cd "${IKALIBR_ROOT_PATH}/thirdparty/ctraj/thirdparty/tiny-viewer" || exit

if [ -f "${IKALIBR_ROOT_PATH}/patches/tiny-viewer-opengl-fix.patch" ]; then
    echo "Applying OpenGL fix patch..."
    # Check if the fix is already applied
    if ! grep -q "find_package(OpenGL REQUIRED COMPONENTS OpenGL)" src/CMakeLists.txt; then
        patch -p1 -N -f < "${IKALIBR_ROOT_PATH}/patches/tiny-viewer-opengl-fix.patch" 2>/dev/null || true
    else
        echo "OpenGL fix already applied, skipping patch."
    fi
fi

if [ -f "${IKALIBR_ROOT_PATH}/patches/tiny-viewer-optional-fix.patch" ]; then
    echo "Applying optional include fix patch..."
    # Check if the fix is already applied
    if ! grep -q "#include <optional>" src/include/tiny-viewer/entity/utils.h; then
        patch -p1 -N -f < "${IKALIBR_ROOT_PATH}/patches/tiny-viewer-optional-fix.patch" 2>/dev/null || true
    else
        echo "Optional include fix already applied, skipping patch."
    fi
fi

mkdir "${IKALIBR_ROOT_PATH}/thirdparty/ctraj/thirdparty/tiny-viewer-build"
# shellcheck disable=SC2164
cd "${IKALIBR_ROOT_PATH}/thirdparty/ctraj/thirdparty/tiny-viewer-build"

cmake -DCMAKE_PREFIX_PATH="${IKALIBR_ROOT_PATH}/.pixi/envs/default" -DOpenGL_GL_PREFERENCE=LEGACY -DCMAKE_FIND_PACKAGE_PREFER_CONFIG=ON -DCMAKE_POLICY_DEFAULT_CMP0167=NEW ../tiny-viewer
# echo current path: $PWD
# echo "-----------------------------"
# echo "start making 'tiny-viewer'..."
# echo "-----------------------------"
# make -j8
# cmake --install . --prefix "${IKALIBR_ROOT_PATH}/thirdparty/ctraj/thirdparty/tiny-viewer-install"

# # build ctraj
# echo "----------------------------"
# echo "build thirdparty: 'ctraj'..."
# echo "----------------------------"

# mkdir ${IKALIBR_ROOT_PATH}/thirdparty/ctraj-build
# # shellcheck disable=SC2164
# cd "${IKALIBR_ROOT_PATH}"/thirdparty/ctraj-build

# cmake -DCMAKE_PREFIX_PATH="${IKALIBR_ROOT_PATH}/.pixi/envs/default" ../ctraj # -DOpenGL_GL_PREFERENCE=LEGACY -DCMAKE_FIND_PACKAGE_PREFER_CONFIG=ON -DCMAKE_POLICY_DEFAULT_CMP0167=NEW 
# echo current path: $PWD
# echo "-----------------------"
# echo "start making 'ctraj'..."
# echo "-----------------------"
# make -j8
# cmake --install . --prefix "${IKALIBR_ROOT_PATH}/thirdparty/ctraj-install"

# # build ufomap
# echo "-----------------------------"
# echo "build thirdparty: 'ufomap'..."
# echo "-----------------------------"

# # shellcheck disable=SC2164
# cd "${IKALIBR_ROOT_PATH}"/thirdparty/ufomap
# git checkout origin/devel_surfel

# mkdir ${IKALIBR_ROOT_PATH}/thirdparty/ufomap-build
# # shellcheck disable=SC2164
# cd "${IKALIBR_ROOT_PATH}"/thirdparty/ufomap-build

# cmake -DCMAKE_PREFIX_PATH="${IKALIBR_ROOT_PATH}/.pixi/envs/default" ../ufomap/ufomap
# echo current path: $PWD
# echo "------------------------"
# echo "start making 'ufomap'..."
# echo "------------------------"
# make -j8
# cmake --install . --prefix "${IKALIBR_ROOT_PATH}/thirdparty/ufomap-install"

# # build veta
# echo "---------------------------"
# echo "build thirdparty: 'veta'..."
# echo "---------------------------"

# mkdir ${IKALIBR_ROOT_PATH}/thirdparty/veta-build
# # shellcheck disable=SC2164
# cd "${IKALIBR_ROOT_PATH}"/thirdparty/veta-build

# cmake ../veta
# echo current path: $PWD
# echo "----------------------"
# echo "start making 'veta'..."
# echo "----------------------"
# make -j8
# cmake --install . --prefix "${IKALIBR_ROOT_PATH}/thirdparty/veta-install"

# # build opengv
# echo "-----------------------------"
# echo "build thirdparty: 'opengv'..."
# echo "-----------------------------"

# mkdir ${IKALIBR_ROOT_PATH}/thirdparty/opengv-build
# # shellcheck disable=SC2164
# cd "${IKALIBR_ROOT_PATH}"/thirdparty/opengv-build

# cmake -DCMAKE_POLICY_VERSION_MINIMUM=3.5 ../opengv
# echo current path: $PWD
# echo "------------------------"
# echo "start making 'opengv'..."
# echo "------------------------"
# make -j8
# cmake --install . --prefix "${IKALIBR_ROOT_PATH}/thirdparty/opengv-install"
