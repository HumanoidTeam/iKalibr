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

colmap feature_extractor --database_path ./database.db --image_path ../images --ImageReader.camera_model PINHOLE --ImageReader.single_camera 1 --ImageReader.camera_params 736.428,736.428,921.505,768.216

colmap sequential_matcher --database_path ./database.db --SequentialMatching.overlap 7 --SequentialMatching.quadratic_overlap 1

glomap mapper --database_path ./database.db --image_path ../images --output_path .

colmap model_converter --input_path ./0 --output_path . --output_type TXT

cd "$SCRIPT_DIR"

cd head_front_top_camera/image/compressed/sfm_ws

colmap feature_extractor --database_path ./database.db --image_path ../images --ImageReader.camera_model PINHOLE --ImageReader.single_camera 1 --ImageReader.camera_params 735.910,735.910,942.132,775.125

colmap sequential_matcher --database_path ./database.db --SequentialMatching.overlap 7 --SequentialMatching.quadratic_overlap 1

glomap mapper --database_path ./database.db --image_path ../images --output_path .

colmap model_converter --input_path ./0 --output_path . --output_type TXT

cd "$SCRIPT_DIR" 

cd head_left_camera/image/compressed/sfm_ws

colmap feature_extractor --database_path ./database.db --image_path ../images --ImageReader.camera_model PINHOLE --ImageReader.single_camera 1 --ImageReader.camera_params 816.314,816.314,986.068,757.975

colmap sequential_matcher --database_path ./database.db --SequentialMatching.overlap 7 --SequentialMatching.quadratic_overlap 1

glomap mapper --database_path ./database.db --image_path ../images --output_path .

colmap model_converter --input_path ./0 --output_path . --output_type TXT

cd "$SCRIPT_DIR"

cd head_right_camera/image/compressed/sfm_ws

colmap feature_extractor --database_path ./database.db --image_path ../images --ImageReader.camera_model PINHOLE --ImageReader.single_camera 1 --ImageReader.camera_params 818.725,818.725,990.867,758.595

colmap sequential_matcher --database_path ./database.db --SequentialMatching.overlap 7 --SequentialMatching.quadratic_overlap 1

glomap mapper --database_path ./database.db --image_path ../images --output_path .

colmap model_converter --input_path ./0 --output_path . --output_type TXT

cd "$SCRIPT_DIR"

cd head_rear_left_camera/image/compressed/sfm_ws

colmap feature_extractor --database_path ./database.db --image_path ../images --ImageReader.camera_model PINHOLE --ImageReader.single_camera 1 --ImageReader.camera_params 736.146,736.146,918.037,791.080

colmap sequential_matcher --database_path ./database.db --SequentialMatching.overlap 7 --SequentialMatching.quadratic_overlap 1

glomap mapper --database_path ./database.db --image_path ../images --output_path .

colmap model_converter --input_path ./0 --output_path . --output_type TXT

cd "$SCRIPT_DIR"

cd head_rear_right_camera/image/compressed/sfm_ws

colmap feature_extractor --database_path ./database.db --image_path ../images --ImageReader.camera_model PINHOLE --ImageReader.single_camera 1 --ImageReader.camera_params 736.458,736.458,922.390,773.194

colmap sequential_matcher --database_path ./database.db --SequentialMatching.overlap 7 --SequentialMatching.quadratic_overlap 1

glomap mapper --database_path ./database.db --image_path ../images --output_path .

colmap model_converter --input_path ./0 --output_path . --output_type TXT

cd "$SCRIPT_DIR"
