#!/usr/bin/env python3

import sys
import os
import rosbag
from mcap.reader import make_reader
import rospy
import importlib
from collections import defaultdict
import numpy as np
import csv
import binascii

def ros2_to_ros1(ros2_type):
    return ros2_type.replace('/msg/', '/')

def get_msg_class(type_str):
    pkg, msg = type_str.split('/')
    try:
        # Try ROS1 first
        return getattr(importlib.import_module(f"{pkg}.msg"), msg)
    except Exception as e:
        try:
            # Try ROS2 if ROS1 fails
            return getattr(importlib.import_module(f"{pkg}.msg"), msg)
        except Exception as e2:
            print(f"[WARN] Could not import message class for type {type_str}: {e}")
            return None

def build_topic_type_map(reader):
    topic_type_map = {}
    summary = reader.get_summary()
    for channel_id, channel in summary.channels.items():
        schema_id = channel.schema_id
        if schema_id in summary.schemas:
            ros2_type = summary.schemas[schema_id].name
            ros1_type = ros2_to_ros1(ros2_type)
            topic_type_map[channel.topic] = ros1_type
        else:
            print(f"[WARN] No schema found for channel {channel_id} (topic: {channel.topic})")
    return topic_type_map

# Known JPEG header offsets for each camera (from our analysis)
CAMERA_JPEG_OFFSETS = {
    '/head_front_bottom_camera/image/compressed': 16,
    '/head_left_camera/image/compressed': 16,
    '/head_right_camera/image/compressed': 16,
    '/head_rear_left_camera/image/compressed': 16,
    '/head_front_top_camera/image/compressed': 16,
    '/head_rear_right_camera/image/compressed': 16  # All cameras use the same offset after CDR header stripping
}

def strip_ros2_cdr_header(data):
    """Strip ROS2 CDR header from message data.
    
    ROS2 CDR header format:
    - 4 bytes: PL_CDR (0x00 0x01 0x00 0x00) or PL_CDR_LE (0x00 0x00 0x00 0x00)
    - 4 bytes: Options (usually 0)
    - 4 bytes: Message length
    - Variable length: Frame ID string
    - Padding to align to 4 bytes
    """
    if len(data) < 12:
        return data
    
    # Check for CDR header magic
    if (data[:4] == b'\x00\x01\x00\x00' or  # PL_CDR (big endian)
        data[:4] == b'\x00\x00\x00\x00'):   # PL_CDR_LE (little endian)
        
        # Get frame ID length from offset 12
        import struct
        frame_id_length = struct.unpack('<I', data[12:16])[0]
        
        # Calculate total header size including frame ID and padding
        header_size = 16 + frame_id_length + (4 - (frame_id_length % 4)) % 4
        
        # Skip the entire header
        return data[header_size:]
    
    return data

def try_deserialize_ros1(msg_class, data):
    try:
        msg = msg_class()
        msg.deserialize(data)
        return msg
    except Exception:
        return None

def try_deserialize_ros2(msg_class, data):
    try:
        # Strip ROS2 CDR header
        stripped_data = strip_ros2_cdr_header(data)
        if len(stripped_data) < 4:
            return None
        
        msg = msg_class()
        msg.deserialize(stripped_data)
        return msg
    except Exception:
        return None

def create_imu_message_from_raw_data(data, timestamp, topic):
    """Create IMU message by manually parsing the raw data"""
    try:
        from sensor_msgs.msg import Imu
        from geometry_msgs.msg import Quaternion, Vector3
        
        msg = Imu()
        msg.header.stamp = timestamp
        msg.header.frame_id = "cv7_link"  # Default frame ID
        
        # Find the frame_id string to locate the actual data
        import struct
        frame_id_start = 16
        frame_id_length = struct.unpack('<I', data[12:16])[0]  # 9 bytes
        
        # Skip frame_id and find where actual IMU data starts
        data_start = frame_id_start + frame_id_length + (4 - (frame_id_length % 4)) % 4  # Align to 4-byte boundary
        
        # Parse quaternion (4 doubles = 32 bytes)
        qx = struct.unpack('<d', data[data_start:data_start+8])[0]
        qy = struct.unpack('<d', data[data_start+8:data_start+16])[0]
        qz = struct.unpack('<d', data[data_start+16:data_start+24])[0]
        qw = struct.unpack('<d', data[data_start+24:data_start+32])[0]
        
        # Parse angular velocity (3 doubles = 24 bytes)
        av_start = data_start + 32
        avx = struct.unpack('<d', data[av_start:av_start+8])[0]
        avy = struct.unpack('<d', data[av_start+8:av_start+16])[0]
        avz = struct.unpack('<d', data[av_start+16:av_start+24])[0]
        
        # Parse linear acceleration (3 doubles = 24 bytes)
        la_start = av_start + 24
        lax = struct.unpack('<d', data[la_start:la_start+8])[0]
        lay = struct.unpack('<d', data[la_start+8:la_start+16])[0]
        laz = struct.unpack('<d', data[la_start+16:la_start+24])[0]
        
        # Set the message fields
        msg.orientation.x = qx
        msg.orientation.y = qy
        msg.orientation.z = qz
        msg.orientation.w = qw
        
        msg.angular_velocity.x = avx
        msg.angular_velocity.y = avy
        msg.angular_velocity.z = avz
        
        msg.linear_acceleration.x = lax
        msg.linear_acceleration.y = lay
        msg.linear_acceleration.z = laz
        
        # Set covariance matrices to identity
        msg.orientation_covariance = [0.01, 0, 0, 0, 0.01, 0, 0, 0, 0.01]
        msg.angular_velocity_covariance = [0.01, 0, 0, 0, 0.01, 0, 0, 0, 0.01]
        msg.linear_acceleration_covariance = [0.01, 0, 0, 0, 0.01, 0, 0, 0, 0.01]
        
        return msg
            
    except Exception as e:
        print(f"[DEBUG] Failed to create IMU message: {e}")
        return None

def validate_jpeg(data):
    """Validate JPEG data and ensure it has proper markers."""
    if len(data) < 4:
        return False
        
    # Check for JPEG start marker
    if data[:2] != b'\xFF\xD8':
        return False
        
    # Check for JPEG end marker
    if data[-2:] != b'\xFF\xD9':
        return False
        
    # Check for basic JPEG structure (should have at least one segment after SOI)
    if len(data) < 6 or data[2] != 0xFF:
        return False
        
    return True

def fix_jpeg_byte_order(data):
    """Try to fix JPEG byte order if needed."""
    # Check if data needs byte swapping
    if len(data) >= 4:
        # Check if bytes are swapped (FF D8 becomes D8 FF)
        if data[0] == 0xD8 and data[1] == 0xFF:
            # Swap bytes in pairs
            fixed = bytearray()
            for i in range(0, len(data)-1, 2):
                fixed.extend([data[i+1], data[i]])
            return bytes(fixed)
    return data

def create_compressed_image_message(data, timestamp, topic):
    try:
        from sensor_msgs.msg import CompressedImage
        msg = CompressedImage()
        msg.header.stamp = timestamp
        msg.header.frame_id = topic.split('/')[1]  # e.g., 'head_rear_right_camera'
        msg.format = 'jpeg'
        
        # Strip CDR header first for all cameras
        stripped_data = strip_ros2_cdr_header(data)
        
        # All cameras have JPEG data at offset 16 after CDR header stripping
        offset = 16
        if len(stripped_data) <= offset:
            print(f"[WARN] Data too small for topic {topic} (need > {offset} bytes, got {len(stripped_data)})")
            return None
            
        # Extract JPEG data starting at the offset
        jpeg_data = stripped_data[offset:]
        
        # Verify JPEG header (should start with 0xFFD8)
        if len(jpeg_data) < 2 or jpeg_data[:2] != b'\xFF\xD8':
            print(f"[WARN] Invalid JPEG header for {topic}")
            return None
            
        msg.data = jpeg_data
        return msg
            
    except Exception as e:
        print(f"[ERROR] Failed to create compressed image message for {topic}: {e}")
        return None

def convert_mcap_to_bag(mcap_path, bag_path, csv_path=None):
    print(f"Converting {mcap_path} to {bag_path}")
    if csv_path:
        print(f"Also exporting IMU data to {csv_path}")
    
    out_dir = os.path.dirname(bag_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Prepare CSV file for IMU data
    csv_writer = None
    csv_file = None
    if csv_path:
        csv_file = open(csv_path, 'w', newline='')
        csv_writer = csv.writer(csv_file)
        # Write CSV header
        csv_writer.writerow([
            'timestamp', 'ros_time', 'topic',
            'orientation_x', 'orientation_y', 'orientation_z', 'orientation_w',
            'angular_velocity_x', 'angular_velocity_y', 'angular_velocity_z',
            'linear_acceleration_x', 'linear_acceleration_y', 'linear_acceleration_z'
        ])

    with rosbag.Bag(bag_path, 'w') as bag:
        reader = make_reader(open(mcap_path, 'rb'))
        topic_type_map = build_topic_type_map(reader)
        msg_class_cache = {}
        failed_topics = set()
        successful_conversions = defaultdict(int)
        skipped_msgs = defaultdict(int)

        print(f"Found {len(topic_type_map)} topics to convert:")
        for topic, msg_type in topic_type_map.items():
            print(f"  {topic}: {msg_type}")

        for schema, channel, message in reader.iter_messages():
            topic = channel.topic
            ros1_type = topic_type_map.get(topic)
            if not ros1_type:
                if topic not in failed_topics:
                    print(f"[WARN] No type info for topic {topic}, skipping.")
                    failed_topics.add(topic)
                continue
            
            if ros1_type not in msg_class_cache:
                msg_class_cache[ros1_type] = get_msg_class(ros1_type)
            msg_class = msg_class_cache[ros1_type]
            if not msg_class:
                if topic not in failed_topics:
                    print(f"[WARN] Could not import message class for {ros1_type}, skipping topic {topic}.")
                    failed_topics.add(topic)
                continue
            
            timestamp = rospy.Time.from_sec(message.log_time / 1e9)
            msg = None
            
            # Handle CompressedImage messages
            if 'CompressedImage' in ros1_type:
                msg = create_compressed_image_message(message.data, timestamp, topic)
            # Handle IMU messages
            elif 'Imu' in ros1_type:
                msg = create_imu_message_from_raw_data(message.data, timestamp, topic)
                if msg and csv_writer:
                    csv_writer.writerow([
                        message.log_time, message.publish_time, topic,
                        msg.orientation.x, msg.orientation.y, msg.orientation.z, msg.orientation.w,
                        msg.angular_velocity.x, msg.angular_velocity.y, msg.angular_velocity.z,
                        msg.linear_acceleration.x, msg.linear_acceleration.y, msg.linear_acceleration.z
                    ])
            
            if msg:
                bag.write(topic, msg, timestamp)
                successful_conversions[topic] += 1
            else:
                skipped_msgs[topic] += 1
                continue
        
        print(f"\nConversion Summary:")
        print(f"Successfully converted topics:")
        for topic, count in successful_conversions.items():
            print(f"  {topic}: {count} messages")
        if skipped_msgs:
            print(f"Skipped messages:")
            for topic, count in skipped_msgs.items():
                print(f"  {topic}: {count} messages skipped")
        if failed_topics:
            print(f"Failed topics: {list(failed_topics)}")
        if csv_path:
            print(f"IMU data exported to CSV: {sum(1 for topic, count in successful_conversions.items() if 'imu' in topic.lower())} messages")
    
    if csv_file:
        csv_file.close()
        print(f"IMU CSV file saved to: {csv_path}")
    
    print(f"Conversion complete! Output saved to {bag_path}")

if __name__ == "__main__":
    # Default paths
    default_mcap = "/home/developer/datasets/hmnd-data/record_test1_0.mcap"
    default_bag = "/home/developer/datasets/hmnd-data/updated.bag"
    default_csv = "/home/developer/datasets/hmnd-data/updated.csv"
    
    if len(sys.argv) < 3:
        print(f"Using default paths:")
        print(f"  MCAP: {default_mcap}")
        print(f"  BAG:  {default_bag}")
        print(f"  CSV:  {default_csv}")
        print(f"\nTo use custom paths: python3 mcap_to_bag_fixed_offsets.py <input.mcap> <output.bag> [output_imu.csv]")
        
        mcap_path = os.path.abspath(os.path.expandvars(os.path.expanduser(default_mcap)))
        bag_path = os.path.abspath(os.path.expandvars(os.path.expanduser(default_bag)))
        csv_path = os.path.abspath(os.path.expandvars(os.path.expanduser(default_csv)))
    else:
        mcap_path = os.path.abspath(os.path.expandvars(os.path.expanduser(sys.argv[1])))
        bag_path = os.path.abspath(os.path.expandvars(os.path.expanduser(sys.argv[2])))
        csv_path = None
        if len(sys.argv) > 3:
            csv_path = os.path.abspath(os.path.expandvars(os.path.expanduser(sys.argv[3])))
    
    print(f"Resolved MCAP path: {mcap_path}")
    print(f"Resolved BAG path: {bag_path}")
    if csv_path:
        print(f"Resolved CSV path: {csv_path}")
    
    if not os.path.exists(mcap_path):
        print(f"Error: MCAP file {mcap_path} does not exist")
        sys.exit(1)
    
    convert_mcap_to_bag(mcap_path, bag_path, csv_path) 