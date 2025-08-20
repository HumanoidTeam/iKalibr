#!/usr/bin/env python3

import sys
import yaml
import numpy as np
from urdf_parser_py.urdf import URDF
import transforms3d
import argparse

def round_to_5(value):
    """Round a value to 5 decimal places."""
    return round(float(value), 5)

def quaternion_from_matrix(matrix):
    """Convert rotation matrix to quaternion."""
    # Extract rotation matrix
    R = matrix[:3, :3]
    # Convert to quaternion (w, x, y, z)
    q = transforms3d.quaternions.mat2quat(R)
    # Return as dictionary with float values rounded to 5 decimal places
    return {
        'qw': round_to_5(q[0]),
        'qx': round_to_5(q[1]),
        'qy': round_to_5(q[2]),
        'qz': round_to_5(q[3])
    }

def position_from_matrix(matrix):
    """Extract position from transformation matrix."""
    pos = matrix[:3, 3]
    return {
        'r0c0': round_to_5(pos[0]),
        'r1c0': round_to_5(pos[1]),
        'r2c0': round_to_5(pos[2])
    }

def get_transform_to_imu(robot, link_name, imu_link_name='head_imu'):
    """Get transformation from a link to IMU frame."""
    def get_chain_to_root(link, chain=None):
        if chain is None:
            chain = []
        parent_joint = None
        for joint in robot.joints:
            if joint.child == link:
                parent_joint = joint
                break
        if parent_joint is None:
            return chain
        chain.append(parent_joint)
        return get_chain_to_root(parent_joint.parent, chain)

    # Get transforms for both chains
    link_chain = get_chain_to_root(link_name)
    imu_chain = get_chain_to_root(imu_link_name)

    # Process camera chain
    link_transform = np.eye(4)
    for joint in link_chain:  # Process chain from tip to root
        xyz = joint.origin.xyz if hasattr(joint.origin, 'xyz') else [0, 0, 0]
        rpy = joint.origin.rpy if hasattr(joint.origin, 'rpy') else [0, 0, 0]
        
        # Create rotation matrix from RPY
        R = transforms3d.euler.euler2mat(rpy[0], rpy[1], rpy[2], 'sxyz')
        
        # Create transformation matrix
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = xyz
        
        # Update transform chain
        link_transform = np.dot(T, link_transform)

    # Process IMU chain
    imu_transform = np.eye(4)
    for joint in imu_chain:  # Process chain from tip to root
        xyz = joint.origin.xyz if hasattr(joint.origin, 'xyz') else [0, 0, 0]
        rpy = joint.origin.rpy if hasattr(joint.origin, 'rpy') else [0, 0, 0]
        
        # Create rotation matrix from RPY
        R = transforms3d.euler.euler2mat(rpy[0], rpy[1], rpy[2], 'sxyz')
        
        # Create transformation matrix
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = xyz
        
        # Update transform chain
        imu_transform = np.dot(T, imu_transform)

    # Get transform from camera to IMU
    # First invert the IMU transform
    imu_transform_inv = np.linalg.inv(imu_transform)
    
    # Then compute the final transform (camera in IMU frame)
    final_transform = np.dot(imu_transform_inv, link_transform)
    
    return final_transform

def create_prior_yaml(urdf_file):
    """Create prior.yaml from URDF file."""
    # Load URDF
    robot = URDF.from_xml_file(urdf_file)

    # Initialize prior data structure
    prior_data = {
        'SpatialTemporalPriori': {
            'SO3_Sen1ToSen2': [],
            'POS_Sen1InSen2': [],
            'TO_Sen1ToSen2': [],
            'RS_READOUT': []
        }
    }

    # List of camera links (based on the provided URDF)
    camera_links = [
        'head_front_top_camera',
        'head_front_bottom_camera',
        'head_rear_right_camera',
        'head_rear_left_camera',
        'head_right_camera',
        'head_left_camera'
    ]

    # Process each camera
    for camera in camera_links:
        try:
            # Get transform from camera to IMU
            transform = get_transform_to_imu(robot, camera)
            
            # Extract rotation and position
            rotation_data = quaternion_from_matrix(transform)
            position_data = position_from_matrix(transform)

            # Create entries for SO3 and POS
            topic_name = f"/head_{camera}/image/compressed"
            
            so3_entry = {
                'key': {
                    'first': "/head_" + camera.replace('head_', '') + "/image/compressed",
                    'second': "/imu/data"
                },
                'value': {
                    'qx': rotation_data['qx'],
                    'qy': rotation_data['qy'],
                    'qz': rotation_data['qz'],
                    'qw': rotation_data['qw']
                }
            }
            
            pos_entry = {
                'key': {
                    'first': "/head_" + camera.replace('head_', '') + "/image/compressed",
                    'second': "/imu/data"
                },
                'value': {
                    'r0c0': position_data['r0c0'],
                    'r1c0': position_data['r1c0'],
                    'r2c0': position_data['r2c0']
                }
            }

            prior_data['SpatialTemporalPriori']['SO3_Sen1ToSen2'].append(so3_entry)
            prior_data['SpatialTemporalPriori']['POS_Sen1InSen2'].append(pos_entry)
            
        except Exception as e:
            print(f"Warning: Failed to process camera {camera}: {str(e)}", file=sys.stderr)
            continue

    return prior_data

class PriorYAMLDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)

    def represent_scalar(self, tag, value, style=None):
        if isinstance(value, str) and (value.startswith('/head_') or value == '/imu/data'):
            style = '"'
        return super().represent_scalar(tag, value, style)

def main():
    parser = argparse.ArgumentParser(description='Convert URDF camera frames to prior.yaml')
    parser.add_argument('urdf_file', help='Input URDF file')
    parser.add_argument('output_file', help='Output YAML file')
    args = parser.parse_args()

    try:
        # Generate prior data
        prior_data = create_prior_yaml(args.urdf_file)

        # Write to YAML file with proper formatting
        with open(args.output_file, 'w') as f:
            yaml.dump(prior_data, f, Dumper=PriorYAMLDumper, default_flow_style=False, sort_keys=False, indent=2)
            
        print(f"Successfully wrote prior data to {args.output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()