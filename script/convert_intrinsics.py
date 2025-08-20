#!/usr/bin/env python3

import yaml
import os
import sys
from pathlib import Path


def validate_camera_data(camera_data):
    """Validate that the camera data has all required fields."""
    required_fields = ["image_width", "image_height", "distortion_model", "camera_matrix", "distortion_coefficients"]
    
    for field in required_fields:
        if field not in camera_data:
            raise ValueError(f"Missing required field: {field}")
    
    if camera_data["distortion_model"] != "fisheye":
        raise ValueError(f"Unsupported camera model: {camera_data['distortion_model']}")

def extract_camera_params(camera_data):
    """Extract camera parameters from the aggregated YAML format."""
    # Extract focal length (fx, fy) from camera matrix
    fx = camera_data["camera_matrix"]["data"][0]  # [0][0]
    fy = camera_data["camera_matrix"]["data"][4]  # [1][1]
    
    # Extract principal point (cx, cy) from camera matrix
    cx = camera_data["camera_matrix"]["data"][2]  # [0][2]
    cy = camera_data["camera_matrix"]["data"][5]  # [1][2]
    
    # Extract distortion coefficients (k1, k2, k3, k4)
    k1, k2, k3, k4 = camera_data["distortion_coefficients"]["data"][:4]
    
    return {
        "width": camera_data["image_width"],
        "height": camera_data["image_height"],
        "model": "OPENCV_FISHEYE",
        "intrinsics": {
            "fx": fx,
            "fy": fy,
            "cx": cx,
            "cy": cy,
            "k1": k1,
            "k2": k2,
            "k3": k3,
            "k4": k4
        }
    }

def convert_camera_to_yaml(camera_data):
    """Convert camera data to iKalibr YAML format."""
    validate_camera_data(camera_data)
    params = extract_camera_params(camera_data)
    
    yaml_data = {
        "Intrinsics": {
            "polymorphic_id": 2147483649,  # Fixed value as per template
            "polymorphic_name": "pinhole_fisheye",  # Fixed value as per template
            "ptr_wrapper": {
                "id": 2147483649,  # Fixed value as per template
                "data": {
                    "img_width": params["width"],
                    "img_height": params["height"],
                    "focal_length": [
                        params["intrinsics"]["fx"],
                        params["intrinsics"]["fy"]
                    ],
                    "principal_point": [
                        params["intrinsics"]["cx"],
                        params["intrinsics"]["cy"]
                    ],
                    "disto_param": [
                        params["intrinsics"]["k1"],
                        params["intrinsics"]["k2"],
                        params["intrinsics"]["k3"],
                        params["intrinsics"]["k4"]
                    ]
                }
            }
        }
    }
    return yaml_data

def save_yaml_file(data, output_path):
    """Save YAML data to file."""
    # Convert to YAML with specific style to match template
    yaml_str = yaml.dump(data, default_flow_style=False, default_style=None)
    
    # Save to file
    with open(output_path, 'w') as f:
        f.write(yaml_str)

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 convert_intrinsics.py <input_yaml> <output_dir>")
        sys.exit(1)
    
    input_yaml = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Read input YAML
    with open(input_yaml, 'r') as f:
        data = yaml.safe_load(f)
    
    # Process each camera
    for camera_name, camera_data in data.items():
        output_filename = f"{camera_name}-intrinsics.yaml"
        output_path = os.path.join(output_dir, output_filename)
        
        # Convert and save
        yaml_data = convert_camera_to_yaml(camera_data)
        save_yaml_file(yaml_data, output_path)
        print(f"Created {output_path}")

if __name__ == "__main__":
    main()
