#############################################
# Stage: base
#############################################
FROM nvidia/cuda:11.8.0-devel-ubuntu20.04 AS base

ARG DEBIAN_FRONTEND=noninteractive

ENV TZ=Etc/UTC \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics \
    DISPLAY=:0 \
    XDG_RUNTIME_DIR=/tmp

SHELL ["/bin/bash", "-lc"]

RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo ca-certificates gnupg2 lsb-release software-properties-common \
    build-essential git curl wget pkg-config \
    python3 python3-pip python3-dev python3-venv \
    bash-completion unzip zip ninja-build \
    && rm -rf /var/lib/apt/lists/*

#############################################
# Stage: deps (system libraries)
#############################################
FROM base AS deps

RUN apt-get update && apt-get install -y --no-install-recommends \
    mesa-utils libgl1-mesa-glx libgl1-mesa-dev \
    libglew-dev libglfw3-dev libxi-dev libxmu-dev libxrandr-dev libxinerama-dev \
    xorg-dev \
    qtbase5-dev libqt5opengl5-dev \
    libboost-all-dev libgoogle-glog-dev libgflags-dev libflann-dev libsqlite3-dev libmetis-dev libfmt-dev \
    libatlas-base-dev libsuitesparse-dev \
    libfreeimage-dev libprotobuf-dev protobuf-compiler \
    libcgal-dev \
    libyaml-cpp-dev libcereal-dev \
    && rm -rf /var/lib/apt/lists/*

#############################################
# Stage: toolchain (CMake, Eigen, Ceres)
#############################################
FROM deps AS toolchain

WORKDIR /tmp/build

# CMake (from Kitware APT for speed and reliability)
RUN apt-get update && apt-get install -y --no-install-recommends \
      apt-transport-https ca-certificates gnupg2 software-properties-common lsb-release \
    && curl -fsSL https://apt.kitware.com/keys/kitware-archive-latest.asc | gpg --dearmor | tee /usr/share/keyrings/kitware-archive-keyring.gpg >/dev/null \
    && echo "deb [signed-by=/usr/share/keyrings/kitware-archive-keyring.gpg] https://apt.kitware.com/ubuntu/ $(lsb_release -cs) main" > /etc/apt/sources.list.d/kitware.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends cmake \
    && rm -rf /var/lib/apt/lists/*

# Eigen 3.4.0
RUN wget -q https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-3.4.0.tar.gz && \
    tar -xzf eigen-3.4.0.tar.gz && cd eigen-3.4.0 && \
    mkdir build && cd build && cmake .. && make -j"$(nproc)" && \
    make install && cd /tmp/build && rm -rf eigen-3.4.0 eigen-3.4.0.tar.gz

# Ceres 2.2.0 (+glog guard)
RUN git clone --branch 2.2.0 --single-branch --recurse-submodules https://github.com/ceres-solver/ceres-solver && \
    cd ceres-solver && mkdir build && cd build && \
    cmake .. -GNinja && ninja && ninja install && \
    cd /tmp/build && rm -rf ceres-solver && \
    CERES_GLOG_CMAKE=/usr/local/lib/cmake/Ceres/FindGlog.cmake; \
    if [ -f "$CERES_GLOG_CMAKE" ]; then \
      sed -i '/add_library(glog::glog INTERFACE IMPORTED)/i if(NOT TARGET glog::glog)' "$CERES_GLOG_CMAKE" && \
      sed -i '/target_link_libraries(glog::glog INTERFACE ${GLOG_LIBRARY})/a endif()' "$CERES_GLOG_CMAKE"; \
    fi

#############################################
# Stage: colmap (COLMAP + GLOMAP)
#############################################
FROM toolchain AS colmap

WORKDIR /tmp/build

RUN git clone --depth 1 --recursive https://github.com/colmap/colmap.git && \
    cd colmap && mkdir build && cd build && \
    cmake .. -GNinja -DCMAKE_BUILD_TYPE=Release -DCUDA_ENABLED=ON && \
    ninja && ninja install && \
    cd /tmp/build && rm -rf colmap

RUN git clone --depth 1 --recursive https://github.com/colmap/glomap.git && \
    cd glomap && mkdir build && cd build && \
    cmake .. -GNinja -DCMAKE_BUILD_TYPE=Release && \
    ninja && ninja install && \
    cd /tmp/build && rm -rf glomap

#############################################
# Stage: sophus (Sophus only)
#############################################
FROM toolchain AS sophus

WORKDIR /tmp/build

RUN git clone --branch 1.22.10 --single-branch https://github.com/strasdat/Sophus.git && \
    cd Sophus && mkdir build && cd build && \
    cmake .. -DSOPHUS_USE_BASIC_LOGGING=ON -DBUILD_TESTING=OFF -DSOPHUS_BUILD_EXAMPLES=OFF -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -GNinja && \
    ninja && ninja install && \
    cd /tmp/build && rm -rf Sophus

#############################################
# Stage: full (ROS, extras, user, devcontainer setup)
#############################################
FROM sophus AS full

# Extras used by iKalibr
WORKDIR /tmp/build

# Sophus (avoid fmt conflict)
RUN git clone --branch 1.22.10 --single-branch https://github.com/strasdat/Sophus.git && \
    cd Sophus && mkdir build && cd build && \
    cmake .. -DSOPHUS_USE_BASIC_LOGGING=ON -DBUILD_TESTING=OFF -DSOPHUS_BUILD_EXAMPLES=OFF -GNinja && \
    ninja && ninja install && \
    cd /tmp/build && rm -rf Sophus

# magic_enum
RUN git clone --branch v0.9.6 --single-branch https://github.com/Neargye/magic_enum.git && \
    cd magic_enum && mkdir build && cd build && \
    cmake .. -GNinja && ninja && ninja install && \
    cd /tmp/build && rm -rf magic_enum

# spdlog (use bundled fmt)
RUN git clone https://github.com/gabime/spdlog.git && \
    cd spdlog && mkdir build && cd build && \
    cmake .. -DSPDLOG_FMT_EXTERNAL=OFF -GNinja && ninja && ninja install && \
    cd /tmp/build && rm -rf spdlog

# Pangolin v0.8
RUN git clone --branch v0.8 --single-branch --recursive https://github.com/stevenlovegrove/Pangolin.git && \
    cd Pangolin && mkdir build && cd build && \
    cmake .. -GNinja && ninja && ninja install && \
    cd /tmp/build && rm -rf Pangolin

# ROS Noetic (Ubuntu 20.04)
RUN sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros1-latest.list' && \
    curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | apt-key add - && \
    apt-get update && apt-get install -y --no-install-recommends \
    ros-noetic-desktop-full \
    ros-noetic-cv-bridge ros-noetic-velodyne \
    && rm -rf /var/lib/apt/lists/* && \
    echo "source /opt/ros/noetic/setup.bash" >> /etc/bash.bashrc

# Python extras
RUN python3 -m pip install --no-cache-dir mcap

# Node.js 18
RUN apt-get update && apt-get remove -y nodejs || true && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user matching common host UID 1000
RUN groupadd -g 1000 developer && \
    useradd -u 1000 -g 1000 -m -s /bin/bash developer && \
    echo "developer ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Prepare workspace directories
RUN mkdir -p /home/iKalibr/src/ikalibr /tmp/.X11-unix /home/developer/datasets /root/datasets && \
    chown -R developer:developer /home/developer /home/iKalibr /tmp/.X11-unix

# Copy optional build helper from repo if present
COPY build_ikalibr.sh /home/developer/build_ikalibr.sh
RUN chmod +x /home/developer/build_ikalibr.sh || true && \
    chown developer:developer /home/developer/build_ikalibr.sh || true

# Switch to developer
USER developer

# Ensure HOME/USER env like previous image
ENV HOME=/home/developer
ENV USER=developer

# Quality-of-life shell setup
RUN git config --global safe.directory '*' && \
    echo 'source /etc/profile.d/bash_completion.sh' >> /home/developer/.bashrc && \
    echo 'if [ -f /etc/bash_completion ]; then . /etc/bash_completion; fi' >> /home/developer/.bashrc && \
    echo 'if [ -f /opt/ros/noetic/setup.bash ]; then source /opt/ros/noetic/setup.bash; fi' >> /home/developer/.bashrc && \
    echo 'if [ -f /home/iKalibr/devel/setup.bash ]; then source /home/iKalibr/devel/setup.bash; fi' >> /home/developer/.bashrc

WORKDIR /home/iKalibr

CMD ["/bin/bash"]

#############################################
# Stage: full_prebuilt (use prebuilt COLMAP)
#############################################
FROM sophus AS full_prebuilt

# Extras used by iKalibr
WORKDIR /tmp/build

# Sophus (avoid fmt conflict)
RUN git clone --branch 1.22.10 --single-branch https://github.com/strasdat/Sophus.git && \
    cd Sophus && mkdir build && cd build && \
    cmake .. -DSOPHUS_USE_BASIC_LOGGING=ON -GNinja && ninja && ninja install && \
    cd /tmp/build && rm -rf Sophus

# magic_enum
RUN git clone --branch v0.9.6 --single-branch https://github.com/Neargye/magic_enum.git && \
    cd magic_enum && mkdir build && cd build && \
    cmake .. -GNinja && ninja && ninja install && \
    cd /tmp/build && rm -rf magic_enum

# spdlog (use bundled fmt)
RUN git clone https://github.com/gabime/spdlog.git && \
    cd spdlog && mkdir build && cd build && \
    cmake .. -DSPDLOG_FMT_EXTERNAL=OFF -GNinja && ninja && ninja install && \
    cd /tmp/build && rm -rf spdlog

# Pangolin v0.8
RUN git clone --branch v0.8 --single-branch --recursive https://github.com/stevenlovegrove/Pangolin.git && \
    cd Pangolin && mkdir build && cd build && \
    cmake .. -GNinja && ninja && ninja install && \
    cd /tmp/build && rm -rf Pangolin

# ROS Noetic (Ubuntu 20.04)
RUN sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros1-latest.list' && \
    curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | apt-key add - && \
    apt-get update && apt-get install -y --no-install-recommends \
    ros-noetic-desktop-full \
    ros-noetic-cv-bridge ros-noetic-velodyne \
    && rm -rf /var/lib/apt/lists/* && \
    echo "source /opt/ros/noetic/setup.bash" >> /etc/bash.bashrc

# Python extras
RUN python3 -m pip install --no-cache-dir mcap

# Node.js 18
RUN apt-get update && apt-get remove -y nodejs || true && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user matching common host UID 1000
RUN groupadd -g 1000 developer && \
    useradd -u 1000 -g 1000 -m -s /bin/bash developer && \
    echo "developer ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Prepare workspace directories
RUN mkdir -p /home/iKalibr/src/ikalibr /tmp/.X11-unix /home/developer/datasets /root/datasets && \
    chown -R developer:developer /home/developer /home/iKalibr /tmp/.X11-unix

# Copy optional build helper from repo if present
COPY build_ikalibr.sh /home/developer/build_ikalibr.sh
RUN chmod +x /home/developer/build_ikalibr.sh || true && \
    chown developer:developer /home/developer/build_ikalibr.sh || true

# Switch to developer
USER developer

# Ensure HOME/USER env like previous image
ENV HOME=/home/developer
ENV USER=developer

# Quality-of-life shell setup
RUN git config --global safe.directory '*' && \
    echo 'source /etc/profile.d/bash_completion.sh' >> /home/developer/.bashrc && \
    echo 'if [ -f /etc/bash_completion ]; then . /etc/bash_completion; fi' >> /home/developer/.bashrc && \
    echo 'if [ -f /opt/ros/noetic/setup.bash ]; then source /opt/ros/noetic/setup.bash; fi' >> /home/developer/.bashrc && \
    echo 'if [ -f /home/iKalibr/devel/setup.bash ]; then source /home/iKalibr/devel/setup.bash; fi' >> /home/developer/.bashrc

WORKDIR /home/iKalibr

CMD ["/bin/bash"]