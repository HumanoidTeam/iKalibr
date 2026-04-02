# iKalibr Setup Guide

## Prerequisites
- Git
- VS Code or Cursor (recommended)
- Docker
- Docker Compose

## Installation Steps

1. Clone the repository from our fork:
   ```bash
   git clone -b hmnd git@github.com:HumanoidTeam/iKalibr.git
   cd iKalibr
   ```

2. Open the project in VS Code/Cursor:
   - Launch your editor
   - File -> Open Folder -> Select the `iKalibr` directory

3. Set up Development Container:
   - When prompted, click "Reopen in Container" in the popup notification:
   ![Dev Container Prompt](./docs/img/devcontainer-prompt.png)
   - This will build and start the development container (may take a few minutes on first run)
   - Alternatively, you can:
     - Press F1 or Ctrl+Shift+P
     - Type "Reopen in Container"
     - Select "Remote-Containers: Reopen in Container"

4. Wait for the container to build and initialize. Once complete, you'll have a fully configured development environment with all dependencies installed.

## Building iKalibr

1. Once the devcontainer is set up, you should see a ROS1 catkin workspace layout in the explorer:
   ![Catkin Workspace Layout](./docs/img/catkin-workspace.png)
   
   The workspace contains:
   - `build/`: Build artifacts and CMake files
   - `devel/`: Development space with setup files and libraries
   - `src/`: Source code directory
   - `.catkin_workspace`: Catkin workspace marker file

2. Build the project:
   ```bash
   # Build iKalibr
   cd src/ikalibr && ./build_ikalibr.sh
   ```

## Dataset preparation

Now that every thing is built to test if anything running 

### [Optional] iKalibr dataset 
To check if everything is working perfectly run the ikalibr dataset 
   ```bash
   roslaunch ikalibr ikalibr-prog.launch config_path:=/home/iKalibr/src/ikalibr/config/ikalibr-dataset-config.yaml
   ```

### HMND dataset
   
#### Convert ROS2 mcap to ROS1 bag files
   The assumption here is that the $HOME/datasets folder from host computer gets mounted to the container at /home/developer/datasets. If it doesn't exist create it and copy the mcap file there and the rosbag file will be generated in the same folder. 

   ```bash
   cd src/ikalibr && python3 script/mcap_to_bag.py
   ```

   To confirm all the topics are there and same as the mcap file do a rosbag info - 

   ```bash
   $ rosbag info /home/developer/datasets/hmnd-data/updated.bag
   
   path:        /home/developer/datasets/hmnd-data/updated.bag
   version:     2.0
   duration:    23.8s
   start:       Jul 16 2025 17:48:52.02 (1752688132.02)
   end:         Jul 16 2025 17:49:15.85 (1752688155.85)
   size:        282.4 MB
   messages:    6673
   compression: none [360/360 chunks]
   types:       sensor_msgs/CompressedImage [8f7a12909da2c9d3332d540a0977563f]
               sensor_msgs/Imu             [6a62c6daae103f4ff57a132d6f95cec2]
   topics:      /head_front_bottom_camera/image/compressed    714 msgs    : sensor_msgs/CompressedImage
               /head_front_top_camera/image/compressed       715 msgs    : sensor_msgs/CompressedImage
               /head_left_camera/image/compressed            715 msgs    : sensor_msgs/CompressedImage
               /head_rear_left_camera/image/compressed       715 msgs    : sensor_msgs/CompressedImage
               /head_rear_right_camera/image/compressed      715 msgs    : sensor_msgs/CompressedImage
               /head_right_camera/image/compressed           715 msgs    : sensor_msgs/CompressedImage
               /imu/data                                    2384 msgs    : sensor_msgs/Imu
   ```

#### Run iKalibr on this dataset
   ```bash
   roslaunch ikalibr ikalibr-prog.launch config_path:=/home/iKalibr/src/ikalibr/config/hmnd/config.yaml
   ```