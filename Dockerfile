FROM debian:stable-slim

# Install necessary X11 client runtime libraries and Godot dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    git \
    libx11-6 \
    libxcursor1 \
    libxinerama1 \
    libgl1-mesa-glx \
    libglu1-mesa \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxext6 \
    libssl3 \
    libzmq5 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./godot /app/

RUN chmod +x /app/runEnv.x86_64

# Environment variables to disable audio and force software rendering.
ENV SDL_AUDIODRIVER=dummy
ENV GODOT_DISABLE_AUDIO=1
ENV LIBGL_ALWAYS_SOFTWARE=1 

# Environment exposes port 10001 for publishing environment's state and 10002
# for receiving actions from software agents. These need to be mapped to ports
# in the host when running the container (-p 10001:10001 -p 10002:10002).
EXPOSE 10001 10002

# Runs the environment using the GLES2 video driver. (Needed this for X11 rendering on Windows)
CMD ["./runEnv.x86_64", "--video-driver", "GLES2"]
