# Use a Debian base image for stability and ease of installing ffmpeg
# The bullseye-slim tag is a good balance between size and functionality
FROM debian:bullseye-slim

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive

# Install core system dependencies in layers
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libsqlite3-dev \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python and core development tools, including python3-venv
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Update pip
RUN pip3 install --no-cache-dir --upgrade pip

# Create a non-root user for security and development purposes
ARG USERNAME=devuser
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Shorten the terminal prompt (PS1) for the devuser to show only the current directory name (e.g., 'app$ ').
RUN echo "PS1='\\W\\$ '" >> /home/$USERNAME/.bashrc

# Set the working directory
WORKDIR /usr/src/app

# Change ownership of the working directory to the non-root user
RUN chown -R $USERNAME:$USERNAME /usr/src/app

# Switch to the non-root user
USER $USERNAME

# Install the core Python dependencies (yt-dlp, rich, etc.)
RUN pip3 install yt-dlp rich

# Command to keep the container running if needed, or you can let the devcontainer configuration manage this.
CMD ["/bin/bash"]
