#!/bin/bash

# Pass the script the main directory for the images where ikalibr stores the undistorted images to run SfM

# Check if script directory is provided as first argument
if [ $# -eq 0 ]; then
    echo "Usage: $0 <script_directory>"
    echo "Please provide the the main directory for the images where ikalibr has stored the undistorted images for all cameras"

    exit 1
fi

SCRIPT_DIR="$1"

cd "$SCRIPT_DIR"

cd head_front_bottom_camera/image/compressed/sfm_ws

colmap feature_extractor --database_path ./database.db --image_path ../images --ImageReader.camera_model PINHOLE --ImageReader.single_camera 1 --ImageReader.camera_params 365.188,365.188,458.291,383.511

colmap sequential_matcher --database_path ./database.db --SequentialMatching.overlap 7 --SequentialMatching.quadratic_overlap 1

glomap mapper --database_path ./database.db --image_path ../images --output_path .

colmap model_converter --input_path ./0 --output_path . --output_type TXT

cd "$SCRIPT_DIR"

cd head_front_top_camera/image/compressed/sfm_ws

colmap feature_extractor --database_path ./database.db --image_path ../images --ImageReader.camera_model PINHOLE --ImageReader.single_camera 1 --ImageReader.camera_params 369.947,369.947,487.525,380.101

colmap sequential_matcher --database_path ./database.db --SequentialMatching.overlap 7 --SequentialMatching.quadratic_overlap 1

glomap mapper --database_path ./database.db --image_path ../images --output_path .

colmap model_converter --input_path ./0 --output_path . --output_type TXT

cd "$SCRIPT_DIR" 

cd head_left_camera/image/compressed/sfm_ws

colmap feature_extractor --database_path ./database.db --image_path ../images --ImageReader.camera_model PINHOLE --ImageReader.single_camera 1 --ImageReader.camera_params 410.193,410.193,467.069,391.691

colmap sequential_matcher --database_path ./database.db --SequentialMatching.overlap 7 --SequentialMatching.quadratic_overlap 1

glomap mapper --database_path ./database.db --image_path ../images --output_path .

colmap model_converter --input_path ./0 --output_path . --output_type TXT

cd "$SCRIPT_DIR"

cd head_right_camera/image/compressed/sfm_ws

colmap feature_extractor --database_path ./database.db --image_path ../images --ImageReader.camera_model PINHOLE --ImageReader.single_camera 1 --ImageReader.camera_params 410.075,410.075,461.982,388.080

colmap sequential_matcher --database_path ./database.db --SequentialMatching.overlap 7 --SequentialMatching.quadratic_overlap 1

glomap mapper --database_path ./database.db --image_path ../images --output_path .

colmap model_converter --input_path ./0 --output_path . --output_type TXT

cd "$SCRIPT_DIR"

cd head_rear_left_camera/image/compressed/sfm_ws

colmap feature_extractor --database_path ./database.db --image_path ../images --ImageReader.camera_model PINHOLE --ImageReader.single_camera 1 --ImageReader.camera_params 356.687,356.687,459.585,404.333

colmap sequential_matcher --database_path ./database.db --SequentialMatching.overlap 7 --SequentialMatching.quadratic_overlap 1

glomap mapper --database_path ./database.db --image_path ../images --output_path .

colmap model_converter --input_path ./0 --output_path . --output_type TXT

cd "$SCRIPT_DIR"

cd head_rear_right_camera/image/compressed/sfm_ws

colmap feature_extractor --database_path ./database.db --image_path ../images --ImageReader.camera_model PINHOLE --ImageReader.single_camera 1 --ImageReader.camera_params 368.120,368.120,461.231,390.621

colmap sequential_matcher --database_path ./database.db --SequentialMatching.overlap 7 --SequentialMatching.quadratic_overlap 1

glomap mapper --database_path ./database.db --image_path ../images --output_path .

colmap model_converter --input_path ./0 --output_path . --output_type TXT

cd "$SCRIPT_DIR"
