FROM ulong2/ie_kalibr_image:latest

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    python3-pip \
    bash-completion \
    && rm -rf /var/lib/apt/lists/*

# Install mcap
RUN python3 -m pip install --no-cache-dir mcap

# Remove old Node.js and install Node.js 18 with npm from NodeSource
RUN apt-get remove -y nodejs || true \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Create a user with UID 1000 (standard for first user on most Linux systems)
RUN groupadd -g 1000 developer && \
    useradd -u 1000 -g 1000 -m -s /bin/bash developer

# Set up environment variables for Cursor
ENV HOME=/home/developer
ENV USER=developer
ENV DISPLAY=:0
ENV XDG_RUNTIME_DIR=/tmp

# Create necessary directories and set ownership
RUN mkdir -p /home/iKalibr/src/ikalibr /tmp/.X11-unix /home/developer/datasets /root/datasets && \
    chown -R developer:developer /home/developer /home/iKalibr

# Copy and set up the build script
COPY build_ikalibr.sh /home/developer/build_ikalibr.sh
RUN chmod +x /home/developer/build_ikalibr.sh && \
    chown developer:developer /home/developer/build_ikalibr.sh

# Give user sudo access for workspace permissions
RUN echo "developer ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Switch to the user
USER developer

# Configure Git to trust all directories
RUN git config --global safe.directory '*'

# Configure bash completion
RUN echo 'source /etc/profile.d/bash_completion.sh' >> ~/.bashrc && \
    echo 'if [ -f /etc/bash_completion ]; then . /etc/bash_completion; fi' >> ~/.bashrc

# Add ROS workspace sourcing
RUN echo 'if [ -f /home/iKalibr/devel/setup.bash ]; then source /home/iKalibr/devel/setup.bash; fi' >> ~/.bashrc

# Set the working directory to match devcontainer.json
WORKDIR /home/iKalibr

# Keep the container running
CMD ["/bin/bash"] 