#!/usr/bin/env python3

import argparse
import os
import yaml
import shutil
import subprocess
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description='Generate config.yaml with updated camera intrinsics and prior paths')
    parser.add_argument('--intrinsics-folder', type=str, required=True,
                      help='Path to folder containing camera intrinsics files')
    parser.add_argument('--prior-yaml', type=str, required=True,
                      help='Path to prior yaml file')
    parser.add_argument('--output-folder', type=str, required=True,
                      help='Path to output folder where iKalibr results will be saved')
    parser.add_argument('--config-output', type=str, required=True,
                      help='Path to folder where generated config files will be saved')
    parser.add_argument('--rosbag', type=str, required=True,
                      help='Path to input rosbag file')
    parser.add_argument('--template-config', type=str, 
                      default='/home/iKalibr/src/ikalibr/config/hmnd/config.yaml',
                      help='Path to template config.yaml file')
    return parser.parse_args()

def get_rosbag_duration(bag_path):
    """Get the duration of a rosbag file using rosbag info command."""
    try:
        # Source ROS setup.bash first [[memory:4153560]]
        cmd = f"bash -c 'source /home/iKalibr/devel/setup.bash && rosbag info {bag_path}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to get rosbag info: {result.stderr}")
        
        # Parse the output to find duration
        for line in result.stdout.split('\n'):
            if 'duration' in line.lower():
                # Extract duration value (in seconds), handling (Xs) format
                duration_str = line.split()[-1].strip('()s')
                try:
                    duration = float(duration_str)
                    return duration
                except ValueError:
                    continue
                
        raise ValueError("Could not find valid duration in rosbag info output")
        
    except Exception as e:
        raise RuntimeError(f"Error getting rosbag duration: {str(e)}")

def get_camera_name(topic):
    # Extract camera name from topic, e.g., "/head_front_bottom_camera/image/compressed" -> "front_bottom_camera"
    parts = topic.split('/')
    camera_part = parts[1]  # e.g., "head_front_bottom_camera"
    # Remove "head_" prefix but keep "_camera" as it's part of the filename
    camera_name = camera_part.replace('head_', '')
    return camera_name

def update_config(template_path, intrinsics_folder, prior_yaml_path, output_folder, config_output, rosbag_path):
    # Create output folders if they don't exist
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(config_output, exist_ok=True)
    
    # Read template config
    with open(template_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Update camera intrinsics paths
    camera_topics = config['Configor']['DataStream']['CameraTopics']
    for topic_entry in camera_topics:
        topic = topic_entry['key']
        camera_name = get_camera_name(topic)
        intrinsics_file = f"{camera_name}-intrinsics.yaml"
        
        # Verify that the intrinsics file exists
        if not os.path.exists(os.path.join(intrinsics_folder, intrinsics_file)):
            print(f"Warning: Expected intrinsics file {intrinsics_file} not found in {intrinsics_folder}")
        intrinsics_path = os.path.join(intrinsics_folder, intrinsics_file)
        
        # Update the intrinsics path
        topic_entry['value']['Intrinsics'] = intrinsics_path
    
    # Update prior yaml path
    config['Configor']['Prior']['SpatTempPrioriPath'] = prior_yaml_path
    
    # Update rosbag path and duration
    config['Configor']['DataStream']['BagPath'] = rosbag_path
    
    # Get and set rosbag duration
    duration = get_rosbag_duration(rosbag_path)
    config['Configor']['DataStream']['Duration'] = duration
    
    # Set output path to output_folder/ikalibr_output
    ikalibr_output_path = os.path.join(output_folder, 'ikalibr_output')
    config['Configor']['DataStream']['OutputPath'] = ikalibr_output_path
    
    # Save modified config to config_output directory
    output_path = os.path.join(config_output, 'config.yaml')
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"Generated config saved to: {output_path}")
    print(f"Rosbag duration set to: {duration} seconds")
    print(f"iKalibr output will be saved to: {ikalibr_output_path}")

def main():
    args = parse_args()
    
    # Verify input paths exist
    if not os.path.exists(args.intrinsics_folder):
        raise FileNotFoundError(f"Intrinsics folder not found: {args.intrinsics_folder}")
    if not os.path.exists(args.prior_yaml):
        raise FileNotFoundError(f"Prior yaml file not found: {args.prior_yaml}")
    if not os.path.exists(args.template_config):
        raise FileNotFoundError(f"Template config file not found: {args.template_config}")
    if not os.path.exists(args.rosbag):
        raise FileNotFoundError(f"Rosbag file not found: {args.rosbag}")
    
    update_config(args.template_config, args.intrinsics_folder, args.prior_yaml, 
                 args.output_folder, args.config_output, args.rosbag)

if __name__ == "__main__":
    main()