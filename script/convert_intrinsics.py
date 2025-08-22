#!/usr/bin/env python3

import yaml
import json
import os
import sys
from pathlib import Path


def detect_file_format(file_path):
    """Detect if the input file is JSON or YAML based on extension and content."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.json']:
        return 'json'
    elif ext in ['.yaml', '.yml']:
        return 'yaml'
    
    # If extension doesn't clearly indicate, try to parse as JSON first
    try:
        with open(file_path, 'r') as f:
            json.load(f)
            return 'json'
    except json.JSONDecodeError:
        return 'yaml'

def validate_camera_data(camera_data, format_type='yaml'):
    """Validate that the camera data has all required fields."""
    if format_type == 'json':
        # For JSON format from OpenMVG
        if not isinstance(camera_data, dict) or 'intrinsic' not in camera_data:
            raise ValueError("Invalid JSON camera data format")
        
        intrinsic_data = camera_data['intrinsic']['value']['ptr_wrapper']['data']
        if not all(key in intrinsic_data for key in ['width', 'height', 'focal_length', 'principal_point', 'fisheye']):
            raise ValueError("Missing required fields in JSON camera data")
        return
    
    # For YAML format
    required_fields = ["image_width", "image_height", "distortion_model", "camera_matrix", "distortion_coefficients"]
    for field in required_fields:
        if field not in camera_data:
            raise ValueError(f"Missing required field: {field}")
    
    if camera_data["distortion_model"] != "fisheye":
        raise ValueError(f"Unsupported camera model: {camera_data['distortion_model']}")

def extract_camera_params(camera_data, format_type='yaml'):
    """Extract camera parameters from the input format."""
    if format_type == 'json':
        intrinsic_data = camera_data['intrinsic']['value']['ptr_wrapper']['data']
        # In JSON format, focal length is single value, use it for both fx and fy
        fx = fy = intrinsic_data['focal_length']
        cx, cy = intrinsic_data['principal_point']
        k1, k2, k3, k4 = intrinsic_data['fisheye'][:4]
        width = intrinsic_data['width']
        height = intrinsic_data['height']
    else:
        # Extract focal length (fx, fy) from camera matrix
        fx = camera_data["camera_matrix"]["data"][0]  # [0][0]
        fy = camera_data["camera_matrix"]["data"][4]  # [1][1]
        
        # Extract principal point (cx, cy) from camera matrix
        cx = camera_data["camera_matrix"]["data"][2]  # [0][2]
        cy = camera_data["camera_matrix"]["data"][5]  # [1][2]
        
        # Extract distortion coefficients (k1, k2, k3, k4)
        k1, k2, k3, k4 = camera_data["distortion_coefficients"]["data"][:4]
        width = camera_data["image_width"]
        height = camera_data["image_height"]
    
    return {
        "width": width,
        "height": height,
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

def convert_camera_to_yaml(camera_data, format_type='yaml'):
    """Convert camera data to iKalibr YAML format."""
    validate_camera_data(camera_data, format_type)
    params = extract_camera_params(camera_data, format_type)
    
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

def process_json_data(data):
    """Process JSON format data and return a dictionary of camera data."""
    result = {}
    for camera in data.get('cameras', []):
        camera_name = camera.get('camera_name')
        if camera_name:
            result[camera_name] = camera
    return result

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 convert_intrinsics.py <input_file> <output_dir>")
        print("Note: input_file can be either YAML or JSON format")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Detect file format
    format_type = detect_file_format(input_file)
    
    # Read input file
    with open(input_file, 'r') as f:
        if format_type == 'json':
            data = json.load(f)
            data = process_json_data(data)
        else:
            data = yaml.safe_load(f)
    
    # Process each camera
    for camera_name, camera_data in data.items():
        output_filename = f"{camera_name}-intrinsics.yaml"
        output_path = os.path.join(output_dir, output_filename)
        
        # Convert and save
        yaml_data = convert_camera_to_yaml(camera_data, format_type)
        save_yaml_file(yaml_data, output_path)
        print(f"Created {output_path}")

if __name__ == "__main__":
    main()
