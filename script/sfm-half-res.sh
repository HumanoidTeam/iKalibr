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

colmap feature_extractor --database_path ./database.db --image_path ../images --ImageReader.camera_model PINHOLE --ImageReader.single_camera 1 --ImageReader.camera_params 368.096,368.096,460.623,384.337

colmap sequential_matcher --database_path ./database.db --SequentialMatching.overlap 7 --SequentialMatching.quadratic_overlap 1

glomap mapper --database_path ./database.db --image_path ../images --output_path .

colmap model_converter --input_path ./0 --output_path . --output_type TXT

cd "$SCRIPT_DIR"

cd head_front_top_camera/image/compressed/sfm_ws

colmap feature_extractor --database_path ./database.db --image_path ../images --ImageReader.camera_model PINHOLE --ImageReader.single_camera 1 --ImageReader.camera_params 367.863,367.863,470.920,387.547

colmap sequential_matcher --database_path ./database.db --SequentialMatching.overlap 7 --SequentialMatching.quadratic_overlap 1

glomap mapper --database_path ./database.db --image_path ../images --output_path .

colmap model_converter --input_path ./0 --output_path . --output_type TXT

cd "$SCRIPT_DIR" 

cd head_left_camera/image/compressed/sfm_ws

colmap feature_extractor --database_path ./database.db --image_path ../images --ImageReader.camera_model PINHOLE --ImageReader.single_camera 1 --ImageReader.camera_params 408.215,408.215,493.247,378.666

colmap sequential_matcher --database_path ./database.db --SequentialMatching.overlap 7 --SequentialMatching.quadratic_overlap 1

glomap mapper --database_path ./database.db --image_path ../images --output_path .

colmap model_converter --input_path ./0 --output_path . --output_type TXT

cd "$SCRIPT_DIR"

cd head_right_camera/image/compressed/sfm_ws

colmap feature_extractor --database_path ./database.db --image_path ../images --ImageReader.camera_model PINHOLE --ImageReader.single_camera 1 --ImageReader.camera_params 409.317,409.317,495.197,378.689

colmap sequential_matcher --database_path ./database.db --SequentialMatching.overlap 7 --SequentialMatching.quadratic_overlap 1

glomap mapper --database_path ./database.db --image_path ../images --output_path .

colmap model_converter --input_path ./0 --output_path . --output_type TXT

cd "$SCRIPT_DIR"

cd head_rear_left_camera/image/compressed/sfm_ws

colmap feature_extractor --database_path ./database.db --image_path ../images --ImageReader.camera_model PINHOLE --ImageReader.single_camera 1 --ImageReader.camera_params 364.768,364.768,458.302,396.125

colmap sequential_matcher --database_path ./database.db --SequentialMatching.overlap 7 --SequentialMatching.quadratic_overlap 1

glomap mapper --database_path ./database.db --image_path ../images --output_path .

colmap model_converter --input_path ./0 --output_path . --output_type TXT

cd "$SCRIPT_DIR"

cd head_rear_right_camera/image/compressed/sfm_ws

colmap feature_extractor --database_path ./database.db --image_path ../images --ImageReader.camera_model PINHOLE --ImageReader.single_camera 1 --ImageReader.camera_params 368.986,368.986,460.956,386.793

colmap sequential_matcher --database_path ./database.db --SequentialMatching.overlap 7 --SequentialMatching.quadratic_overlap 1

glomap mapper --database_path ./database.db --image_path ../images --output_path .

colmap model_converter --input_path ./0 --output_path . --output_type TXT

cd "$SCRIPT_DIR"
