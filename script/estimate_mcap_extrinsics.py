#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
import json
import yaml
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

def run_command(cmd, description):
    """Run a command and check its return status."""
    print(f"\n=== Running {description} ===")
    print(f"Command: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"Error: {description} failed with return code {result.returncode}")
        sys.exit(1)
    print(f"=== {description} completed successfully ===\n")

def main():
    parser = argparse.ArgumentParser(
        description='Run complete iKalibr calibration pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Using YAML format
    %(prog)s -i intrinsics/aggregated.yaml -m data.mcap -u robot.urdf -o output/

    # Using JSON format
    %(prog)s -i intrinsics/aggregated_intrinsics.json -m data.mcap -u robot.urdf -o output/
""")
    
    # Required arguments
    parser.add_argument('-i', '--input-intrinsics', required=True,
                      help='Input intrinsics file (either aggregated.yaml or aggregated_intrinsics.json)')
    parser.add_argument('-m', '--input-mcap', required=True,
                      help='Input MCAP file')
    parser.add_argument('-u', '--input-urdf', required=True,
                      help='Input URDF file')
    parser.add_argument('-o', '--output-dir', required=True,
                      help='Output directory for all generated files')
    
    # Optional arguments
    parser.add_argument('-r', '--image-rate', type=int, default=3,
                      help='Image rate for mcap_to_bag conversion (default: 3)')
    parser.add_argument('-s', '--imu-rate', type=int, default=1,
                      help='IMU rate for mcap_to_bag conversion (default: 1)')
    parser.add_argument('-z', '--resize', action='store_true', default=True,
                      help='Resize images to half resolution in mcap_to_bag conversion')
    
    args = parser.parse_args()
    
    # Create output directory structure
    output_dir = Path(args.output_dir).resolve()  # Get absolute path
    intrinsics_dir = output_dir / 'intrinsics'
    bag_dir = output_dir / 'bag'
    prior_dir = output_dir / 'prior'
    config_dir = output_dir / 'config'
    calib_dir = output_dir / 'calibration'
    compared_dir = output_dir / 'compared'  # Hardcoded directory for comparison results
    
    # Create all required directories
    directories = [output_dir, intrinsics_dir, bag_dir, prior_dir, config_dir, calib_dir, compared_dir]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Define output files with absolute paths
    bag_file = bag_dir / 'calibration.bag'
    prior_file = prior_dir / 'prior.yaml'
    config_file = config_dir / 'config.yaml'
    calib_param_file = calib_dir / 'ikalibr_output/ikalibr_param.yaml'
    output_urdf = output_dir / 'calibrated.urdf'
    
    # Convert all paths to absolute paths
    bag_file = bag_file.resolve()
    prior_file = prior_file.resolve()
    config_file = config_file.resolve()
    calib_param_file = calib_param_file.resolve()
    output_urdf = output_urdf.resolve()
    
    # 1. Convert intrinsics
    input_intrinsics_file = Path(args.input_intrinsics)
    if not input_intrinsics_file.exists():
        print(f"Error: Input intrinsics file {input_intrinsics_file} not found")
        sys.exit(1)

    # Detect file format
    format_type = detect_file_format(input_intrinsics_file)
    format_desc = "JSON" if format_type == "json" else "YAML"
    print(f"\nDetected {format_desc} format for intrinsics file")

    run_command(
        f"python3 /home/iKalibr/src/ikalibr/script/convert_intrinsics.py {input_intrinsics_file} {intrinsics_dir}",
        "Intrinsics Conversion"
    )
    
    # 2. Convert MCAP to ROS bag (if needed)
    if bag_file.exists():
        print(f"\n=== Skipping MCAP to ROS Bag Conversion ===")
        print(f"ROS bag file already exists at: {bag_file}")
        print(f"Delete the file if you want to regenerate it.")
    else:
        mcap_cmd = [
            "python3 /home/iKalibr/src/ikalibr/script/mcap_to_bag.py",
            f"--mcap {args.input_mcap}",
            f"--bag {bag_file}",
            f"--image-rate {args.image_rate}",
            f"--imu-rate {args.imu_rate}"
        ]
        if args.resize:
            mcap_cmd.append("--resize")
        run_command(" ".join(mcap_cmd), "MCAP to ROS Bag Conversion")
    
    # 3. Generate prior from URDF
    run_command(
        f"python3 /home/iKalibr/src/ikalibr/script/urdf_to_prior.py {args.input_urdf} {prior_file}",
        "URDF to Prior Conversion"
    )
    
    # 4. Generate iKalibr config
    run_command(
        f"python3 /home/iKalibr/src/ikalibr/script/generate_config.py "
        f"--intrinsics-folder {intrinsics_dir} "
        f"--prior-yaml {prior_file} "
        f"--output-folder {calib_dir} "
        f"--config-output {config_dir} "
        f"--rosbag {bag_file}",
        "Config Generation"
    )
    
    # 5. Run iKalibr
    run_command(
        f"bash -c 'source /home/iKalibr/devel/setup.bash && "
        f"roslaunch ikalibr ikalibr-prog.launch config_path:={config_file}'",
        "iKalibr Calibration"
    )
    
    # 6. Convert calibration parameters back to URDF
    # First check if calibration params file exists
    if not calib_param_file.exists():
        print(f"Error: Calibration parameter file not found at {calib_param_file}")
        print("This might indicate that the iKalibr calibration step failed.")
        sys.exit(1)
        
    run_command(
        f"python3 /home/iKalibr/src/ikalibr/script/param_to_urdf.py "
        f"{calib_param_file} {args.input_urdf} {output_urdf} --force "
        f"--compare-with {args.input_urdf} --save-comparison-dir {compared_dir}",
        "Parameter to URDF Conversion"
    )
    
    print("\n=== Calibration Pipeline Completed Successfully ===")
    print(f"Final calibrated URDF: {output_urdf}")
    print("\nGenerated files:")
    print(f"- Converted intrinsics: {intrinsics_dir}")
    print(f"- ROS bag: {bag_file}")
    print(f"- Prior file: {prior_file}")
    print(f"- iKalibr config: {config_file}")
    print(f"- Calibration parameters: {calib_param_file}")
    print(f"- Calibrated URDF: {output_urdf}")

if __name__ == "__main__":
    main()
