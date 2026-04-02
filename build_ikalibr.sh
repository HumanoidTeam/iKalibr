#!/bin/bash

# Build script for iKalibr
# This script automates the build process described in build_ikalibr_docker.md

set -e  # Exit on any error

echo "Starting iKalibr build process..."

source /home/iKalibr/devel/setup.bash

# Navigate to the workspace
cd /home/iKalibr/src/ikalibr

# Build third-party dependencies
if [ -f build_thirdparty.sh ]; then
    echo "Building third-party dependencies..."
    chmod +x build_thirdparty.sh
    ./build_thirdparty.sh
    echo "Third-party dependencies built successfully."
else
    echo "Warning: build_thirdparty.sh not found, skipping third-party build."
fi

# Navigate to the ROS workspace root
cd /home/iKalibr

# Generate messages
echo "Generating ROS messages..."
catkin_make ikalibr_generate_messages

# Compile the project
echo "Compiling iKalibr project..."
catkin_make -j8 -DUSE_CMAKE_UNITY_BUILD=ON

echo "iKalibr build completed successfully!" 