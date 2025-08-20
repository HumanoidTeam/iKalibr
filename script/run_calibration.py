#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
from pathlib import Path

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
    parser = argparse.ArgumentParser(description='Run complete iKalibr calibration pipeline')
    
    # Required arguments
    parser.add_argument('--input-intrinsics', required=True,
                      help='Input YAML file containing camera intrinsics')
    parser.add_argument('--input-mcap', required=True,
                      help='Input MCAP file')
    parser.add_argument('--input-urdf', required=True,
                      help='Input URDF file')
    parser.add_argument('--output-dir', required=True,
                      help='Output directory for all generated files')
    
    # Optional arguments
    parser.add_argument('--image-rate', type=int, default=3,
                      help='Image rate for mcap_to_bag conversion (default: 3)')
    parser.add_argument('--imu-rate', type=int, default=1,
                      help='IMU rate for mcap_to_bag conversion (default: 1)')
    parser.add_argument('--resize', action='store_true',
                      help='Resize images to half resolution in mcap_to_bag conversion')
    
    args = parser.parse_args()
    
    # Create output directory structure
    output_dir = Path(args.output_dir)
    intrinsics_dir = output_dir / 'intrinsics'
    bag_dir = output_dir / 'bag'
    prior_dir = output_dir / 'prior'
    config_dir = output_dir / 'config'
    calib_dir = output_dir / 'calibration'
    
    for directory in [output_dir, intrinsics_dir, bag_dir, prior_dir, config_dir, calib_dir]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Define output files
    bag_file = bag_dir / 'calibration.bag'
    prior_file = prior_dir / 'prior.yaml'
    config_file = config_dir / 'config.yaml'
    calib_param_file = calib_dir / 'calibration_params.yaml'
    output_urdf = output_dir / 'calibrated.urdf'
    
    # 1. Convert intrinsics
    run_command(
        f"python3 /home/iKalibr/src/ikalibr/script/convert_intrinsics.py {args.input_intrinsics} {intrinsics_dir}",
        "Intrinsics Conversion"
    )
    
    # 2. Convert MCAP to ROS bag
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
        f"--output-folder {config_dir} "
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
    run_command(
        f"python3 /home/iKalibr/src/ikalibr/script/param_to_urdf.py "
        f"{calib_param_file} {args.input_urdf} {output_urdf}",
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
