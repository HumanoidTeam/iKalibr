#!/usr/bin/env python3

import sys
import os
import yaml
import csv
import numpy as np
import transforms3d
import argparse
from xml.dom import minidom
from urdf_parser_py.urdf import URDF, Joint, Link, Pose

def create_transform_matrix(xyz, rpy):
    """Create 4x4 transformation matrix from xyz and rpy."""
    # Create rotation matrix from RPY
    R = transforms3d.euler.euler2mat(rpy[0], rpy[1], rpy[2], 'sxyz')
    # Create 4x4 transform
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = xyz
    return T

def transform_matrix_to_rpy_xyz(T):
    """Convert 4x4 transformation matrix to RPY angles and XYZ position."""
    # Extract rotation matrix
    R = T[:3, :3]
    # Convert to euler angles
    rpy = list(transforms3d.euler.mat2euler(R, 'sxyz'))
    # Extract position
    xyz = list(T[:3, 3])
    return rpy, xyz

def rotation_angle_degrees(R_rel):
    """Compute rotation magnitude in degrees from a relative rotation matrix."""
    # Clamp trace-based value for numerical stability
    value = (np.trace(R_rel) - 1.0) / 2.0
    value = float(np.clip(value, -1.0, 1.0))
    return float(np.degrees(np.arccos(value)))

def get_camera_head_transforms(robot):
    """Return dict mapping camera child link -> 4x4 head->camera transform."""
    transforms = {}
    for joint in robot.joints:
        if not hasattr(joint, 'child'):
            continue
        if 'camera' not in joint.child:
            continue
        xyz = joint.origin.xyz if hasattr(joint.origin, 'xyz') else [0, 0, 0]
        rpy = joint.origin.rpy if hasattr(joint.origin, 'rpy') else [0, 0, 0]
        transforms[joint.child] = create_transform_matrix(xyz, rpy)
    return transforms

def write_csv(rows, header, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)

def compare_urdfs_and_save(alpha_path, out_path, save_dir):
    """Compute head-frame and IMU-frame deltas and save as CSVs in save_dir."""
    alpha_robot = URDF.from_xml_file(alpha_path)
    new_robot = URDF.from_xml_file(out_path)

    # Head frame comparisons (use joint origins / head->camera)
    alpha_HC = get_camera_head_transforms(alpha_robot)
    new_HC = get_camera_head_transforms(new_robot)
    cameras = sorted(set(alpha_HC.keys()) & set(new_HC.keys()))

    head_rows = []
    for cam in cameras:
        T_a = alpha_HC[cam]
        T_n = new_HC[cam]
        dxyz = T_n[:3, 3] - T_a[:3, 3]
        R_rel = np.linalg.inv(T_a[:3, :3]) @ T_n[:3, :3]
        rot_deg = rotation_angle_degrees(R_rel)
        head_rows.append([
            cam,
            float(dxyz[0]), float(dxyz[1]), float(dxyz[2]),
            float(np.linalg.norm(dxyz)), float(rot_deg)
        ])

    # IMU frame comparisons (camera->IMU from URDF)
    imu_rows = []
    for cam in cameras:
        T_a_ci = get_transform_to_imu(alpha_robot, cam)
        T_n_ci = get_transform_to_imu(new_robot, cam)
        dxyz = T_n_ci[:3, 3] - T_a_ci[:3, 3]
        R_rel = np.linalg.inv(T_a_ci[:3, :3]) @ T_n_ci[:3, :3]
        rot_deg = rotation_angle_degrees(R_rel)
        imu_rows.append([
            cam,
            float(dxyz[0]), float(dxyz[1]), float(dxyz[2]),
            float(np.linalg.norm(dxyz)), float(rot_deg)
        ])

    # Save CSVs
    head_csv = os.path.join(save_dir, 'comparison_head_frame.csv')
    imu_csv = os.path.join(save_dir, 'comparison_imu_frame.csv')
    header = ['Camera', 'dX (m)', 'dY (m)', 'dZ (m)', '|dT| (m)', 'Rot. Delta (deg)']
    write_csv(head_rows, header, head_csv)
    write_csv(imu_rows, header, imu_csv)
    return head_csv, imu_csv

def quaternion_to_matrix(q):
    """Convert quaternion to rotation matrix.
    
    Args:
        q (dict): Dictionary containing quaternion components (qw, qx, qy, qz)
        
    Returns:
        ndarray: 3x3 rotation matrix
    """
    try:
        # Convert quaternion (w, x, y, z) to rotation matrix
        q_array = np.array([q['qw'], q['qx'], q['qy'], q['qz']])
        # Normalize quaternion
        q_array = q_array / np.linalg.norm(q_array)
        return transforms3d.quaternions.quat2mat(q_array)
    except KeyError as e:
        raise ValueError(f"Invalid quaternion format. Missing component: {e}")
    except Exception as e:
        raise ValueError(f"Failed to convert quaternion to matrix: {e}")

def position_to_xyz(pos):
    """Convert position dictionary to XYZ array.
    
    Args:
        pos (dict): Dictionary containing position components (r0c0, r1c0, r2c0)
        
    Returns:
        list: [x, y, z] coordinates in meters
    """
    try:
        return [
            float(pos['r0c0']),
            float(pos['r1c0']),
            float(pos['r2c0'])
        ]
    except KeyError as e:
        raise ValueError(f"Invalid position format. Missing component: {e}")
    except ValueError as e:
        raise ValueError(f"Invalid position value: {e}")
    except Exception as e:
        raise ValueError(f"Failed to convert position to XYZ: {e}")

def get_transform_matrix(rot_dict, pos_dict):
    """Create 4x4 transformation matrix from rotation and position dictionaries.
    
    Note: This does the exact reverse of urdf_to_prior.py's transform chain:
    - urdf_to_prior.py: T_cam_imu = inv(T_imu_head) * T_cam_head
    - param_to_urdf.py: T_cam_head = T_imu_head * T_cam_imu
    """
    # Get rotation matrix from quaternion
    R = quaternion_to_matrix(rot_dict['value'])
    
    # Get position vector
    t = position_to_xyz(pos_dict['value'])
    
    # Create transform matrix (camera to IMU in iKalibr frame)
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = t
    
    return T  # Return as is - the transform chain will be handled in create_urdf_from_params

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

def create_urdf_from_params(param_file, template_urdf_file):
    """Create URDF from iKalibr parameter file.
    
    Args:
        param_file (str): Path to iKalibr parameter YAML file
        template_urdf_file (str): Path to template URDF file
        
    Returns:
        URDF: Updated URDF object with calibrated transforms
        
    Raises:
        ValueError: If required data is missing or invalid
        FileNotFoundError: If input files don't exist
    """
    # Load the parameter file
    try:
        with open(param_file, 'r') as f:
            params = yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Parameter file not found: {param_file}")
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse parameter file: {e}")
    
    # Load the template URDF
    try:
        robot = URDF.from_xml_file(template_urdf_file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Template URDF file not found: {template_urdf_file}")
    except Exception as e:
        raise ValueError(f"Failed to parse template URDF: {e}")
    
    # Validate parameter file structure
    if 'CalibParam' not in params:
        # Try to parse as direct calibration data
        calib_data = params
    else:
        calib_data = params['CalibParam']
    
    if 'EXTRI' not in calib_data:
        raise ValueError("Invalid parameter file: missing 'EXTRI' section")
    
    extri = calib_data['EXTRI']
    if 'SO3_CmToBr' not in extri or 'POS_CmInBr' not in extri:
        raise ValueError("Invalid parameter file: missing camera extrinsics data")
    
    # Ensure rotations and positions match
    if len(extri['SO3_CmToBr']) != len(extri['POS_CmInBr']):
        raise ValueError("Mismatch between number of rotations and positions in calibration data")
    
    # Track which cameras we've updated
    updated_cameras = set()
    
    # Process each camera transform
    for i, (rot, pos) in enumerate(zip(extri['SO3_CmToBr'], extri['POS_CmInBr'])):
        # Validate matching camera topics
        if rot['key'] != pos['key']:
            raise ValueError(f"Mismatched camera topics for transform {i}")
        
        camera_topic = rot['key']
        # Extract camera name from topic (remove /image/compressed suffix)
        camera_name = camera_topic.split('/')[1]
        # Remove any existing head_ prefix to normalize
        if camera_name.startswith('head_'):
            camera_name = camera_name[5:]
        # Add head_ prefix
        camera_name = 'head_' + camera_name
        
        # Find the corresponding joint in the URDF
        camera_found = False
        for joint in robot.joints:
            if joint.child == camera_name:
                camera_found = True
                # Get camera to IMU transform from calibration
                T_cam_imu = get_transform_matrix(rot, pos)
                
                # Find IMU joint to get IMU to head_pitch_link transform
                T_imu_head = None
                for imu_joint in robot.joints:
                    if imu_joint.child == 'head_imu':
                        # Get IMU to head_pitch_link transform
                        imu_xyz = imu_joint.origin.xyz
                        imu_rpy = imu_joint.origin.rpy
                        T_imu_head = create_transform_matrix(imu_xyz, imu_rpy)
                        print(f"\nIMU to head_pitch_link transform:")
                        print(f"  XYZ: {imu_xyz}")
                        print(f"  RPY: {imu_rpy}")
                        break
                
                if T_imu_head is None:
                    raise ValueError("Could not find IMU joint in URDF")
                
                # Print debug info for camera transform
                print(f"\nTransform chain for {camera_name}:")
                print(f"Camera to IMU transform:")
                R_cam_imu = T_cam_imu[:3, :3]
                t_cam_imu = T_cam_imu[:3, 3]
                rpy_cam_imu = transforms3d.euler.mat2euler(R_cam_imu, 'sxyz')
                print(f"  XYZ: {list(t_cam_imu)}")
                print(f"  RPY: {list(rpy_cam_imu)}")
                
                # The calibration provides Camera->IMU (T_IC) transform.
                # URDF needs Head->Camera (T_HC). From urdf_to_prior:
                #   T_IC = inv(T_HI) * T_HC  =>  T_HC = T_HI * T_IC
                # Here, the IMU joint origin gives T_HI (Head->IMU).
                T_head_cam = np.dot(T_imu_head, T_cam_imu)

                # Convert to RPY and XYZ for URDF storage
                rpy, xyz = transform_matrix_to_rpy_xyz(T_head_cam)

                print(f"Final head_pitch_link to camera transform:")
                print(f"  XYZ: {xyz}")
                print(f"  RPY: {rpy}")
                
                # Update joint origin
                joint.origin = Pose(xyz=xyz, rpy=rpy)
                updated_cameras.add(camera_name)
                break
        
        if not camera_found:
            print(f"Warning: Camera {camera_name} from calibration not found in URDF", file=sys.stderr)
    
    # Check for cameras in URDF that weren't in calibration data
    for joint in robot.joints:
        if 'camera' in joint.child and joint.child not in updated_cameras:
            print(f"Warning: Camera {joint.child} in URDF not found in calibration data", file=sys.stderr)
    
    return robot

def main():
    """Main function to handle command line interface."""
    parser = argparse.ArgumentParser(
        description='Convert iKalibr calibration parameters to URDF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  %(prog)s ikalibr_param.yaml template.urdf output.urdf

This script takes the calibrated extrinsics from an iKalibr parameter file
and updates a template URDF file with the new transforms. The template URDF
provides the basic robot structure while the parameter file provides the
calibrated camera transforms.
        """
    )
    parser.add_argument('param_file', help='Input iKalibr parameter YAML file')
    parser.add_argument('template_urdf', help='Template URDF file to use for structure')
    parser.add_argument('output_file', help='Output URDF file')
    parser.add_argument('--force', '-f', action='store_true',
                       help='Overwrite output file if it exists')
    parser.add_argument('--compare-with', dest='compare_with', default=None,
                       help='Optional baseline URDF to compare against (saves CSV reports)')
    parser.add_argument('--save-comparison-dir', dest='compare_dir', default=None,
                       help='Directory to save comparison CSVs (defaults to output file directory)')
    args = parser.parse_args()

    try:
        # Check if output file exists
        if not args.force and os.path.exists(args.output_file):
            print(f"Error: Output file {args.output_file} already exists. Use --force to overwrite.",
                  file=sys.stderr)
            sys.exit(1)

        # Generate URDF from parameters
        robot = create_urdf_from_params(args.param_file, args.template_urdf)
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(args.output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Write to URDF file
        try:
            with open(args.output_file, 'w') as f:
                # Convert URDF object to XML string
                from xml.etree import ElementTree
                
                # Create the XML element
                root = ElementTree.Element('robot')
                root.set('name', robot.name)
                
                # Add all links
                for link in robot.links:
                    link_elem = ElementTree.SubElement(root, 'link')
                    link_elem.set('name', link.name)
                
                # Add all joints
                for joint in robot.joints:
                    joint_elem = ElementTree.SubElement(root, 'joint')
                    joint_elem.set('name', joint.name)
                    joint_elem.set('type', joint.type)
                    
                    # Add origin if present
                    if joint.origin:
                        origin_elem = ElementTree.SubElement(joint_elem, 'origin')
                        # Handle both dictionary and Pose object formats
                        if isinstance(joint.origin, dict):
                            if 'xyz' in joint.origin:
                                origin_elem.set('xyz', ' '.join(str(x) for x in joint.origin['xyz']))
                            if 'rpy' in joint.origin:
                                origin_elem.set('rpy', ' '.join(str(x) for x in joint.origin['rpy']))
                        else:
                            # Handle Pose object
                            if hasattr(joint.origin, 'xyz'):
                                origin_elem.set('xyz', ' '.join(str(x) for x in joint.origin.xyz))
                            if hasattr(joint.origin, 'rpy'):
                                origin_elem.set('rpy', ' '.join(str(x) for x in joint.origin.rpy))
                    
                    # Add parent
                    parent_elem = ElementTree.SubElement(joint_elem, 'parent')
                    parent_elem.set('link', joint.parent)
                    
                    # Add child
                    child_elem = ElementTree.SubElement(joint_elem, 'child')
                    child_elem.set('link', joint.child)
                
                # Convert to string with pretty formatting
                rough_string = ElementTree.tostring(root, 'utf-8')
                xml_str_formatted = minidom.parseString(rough_string).toprettyxml(indent='  ', encoding='utf-8')
                
                # Write to file (decode bytes to string since we opened file in text mode)
                f.write(xml_str_formatted.decode('utf-8'))
        except IOError as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            sys.exit(1)
            
        print(f"Successfully wrote updated URDF to {args.output_file}")

        # Optional comparison and report saving
        if args.compare_with:
            compare_dir = args.compare_dir or (output_dir if output_dir else '.')
            try:
                head_csv, imu_csv = compare_urdfs_and_save(args.compare_with, args.output_file, compare_dir)
                print(f"Saved comparison CSVs to:\n  {head_csv}\n  {imu_csv}")
            except Exception as e:
                print(f"Warning: Failed to generate comparison reports: {e}", file=sys.stderr)
        
    except FileNotFoundError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
