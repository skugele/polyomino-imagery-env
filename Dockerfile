FROM debian:stable-slim

# Install necessary X11 client runtime libraries and Godot dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    git \
    dos2unix \
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
    xvfb \
    xauth \
    fonts-dejavu-core \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*


# Get Godot Engine binary (GUI enabled)
ARG GODOT_ENGINE=Godot_v3.6.1-stable_x11.64
ARG GODOT_BIN=/usr/local/bin/godot
RUN wget https://github.com/godotengine/godot/releases/download/3.6.1-stable/${GODOT_ENGINE}.zip \
    && unzip ${GODOT_ENGINE}.zip \
    && mv $GODOT_ENGINE $GODOT_BIN \
    && chmod +x $GODOT_BIN \
    && rm ${GODOT_ENGINE}.zip

WORKDIR /app

COPY ./godot /app
COPY ./scripts/docker_run.sh /app

RUN chmod +x /app/docker_run.sh
RUN dos2unix /app/docker_run.sh

# Environment variables to disable audio and force software rendering.
ENV SDL_AUDIODRIVER=dummy
ENV GODOT_DISABLE_AUDIO=1
ENV LIBGL_ALWAYS_SOFTWARE=1 

# Environment exposes port 10001 for publishing environment's state and 10002
# for receiving actions from software agents. These need to be mapped to ports
# in the host when running the container (-p 10001:10001 -p 10002:10002).
EXPOSE 10001 10002

# Runs the environment (mode based on POLYENV_MODE environment variable)
CMD ["./docker_run.sh"]
