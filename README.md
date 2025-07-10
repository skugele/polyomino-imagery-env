# polyomino-imagery-env


## Docker Instructions
Instructions for building a Docker image for this environment and running that
image as a container appear below.

If training software agents, please be aware that this environment exposes port
10001 for publishing the environment's state and 10002 for receiving actions
from software agents. These need to be mapped to ports in the host when running
the container.

The Docker commands given below use default container/host-port mappings (e.g.,
`-p 10001:10001 -p 10002:10002`).

The environment can be run in interactive mode (GUI enabled) or dedicated server mode (GUI disabled) using images created from the supplied DockerFile.

### Building the Docker Image
A Docker image for this environment can be built from a Unix-like CLI by
executing the following command from the top-level project directory.

```
docker build -t polyomino-env:latest .
```

### Running the Docker Container in Interactive Mode (GUI Enabled)
GUI mode is useful for launching the environment for human subjects or for directly monitoring software agents as they interact with the environment.

Ensure that an X11 server is running and execute the following command (based on your OS and terminal) to run the environment in interactive mode:

#### Linux/Unix
```
docker run -d --rm --name polyomino-env -p 10001:10001 -p 10002:10002 -e DISPLAY=$DISPLAY polyomino-env:latest
```

#### Windows (Powershell)
```
docker run -d --rm --name polyomino-env -p 10001:10001 -p 10002:10002 -e DISPLAY=host.docker.internal:0.0 polyomino-env:latest
```

#### Windows (Bash)
```
winpty docker run -d --rm --name polyomino-env -p 10001:10001 -p 10002:10002 -e DISPLAY=host.docker.internal:0.0 polyomino-env:latest
```

### Running the Docker Container in Headless Mode (non-GUI)
Headless mode is useful when training software agents and there is no need to monitor their interactions with the environment. Since the environment's GUI is disabled, all environment interactions must be made via message passing through the environment's exposed ports.

```
docker run -d --rm --name polyomino-env -p 10001:10001 -p 10002:10002 -e POLYENV_MODE='headless' polyomino-env:latest
```
