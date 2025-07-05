FROM debian:stable-slim AS base

RUN apt-get update && apt-get install -y \
    wget unzip git libx11-dev libxcursor-dev libxinerama-dev libgl1-mesa-dev libglu1-mesa-dev libasound2-dev libpulse-dev libudev-dev libxi-dev libxrandr-dev libxrender-dev libxext-dev libssl-dev python3 \
    xvfb \
    x11-xserver-utils libzmq5

COPY ./godot /app

WORKDIR /app

ENV SDL_AUDIODRIVER=dummy
ENV GODOT_DISABLE_AUDIO=1

EXPOSE 10001 10002

CMD xvfb-run ./runEnv.x86_64
