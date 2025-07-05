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

### Building Docker Image
A Docker image for this environment can be built from a Unix-like CLI by
executing the following command from the top-level project directory.
```
docker build -t polyomino-env:latest .
```
### Running Docker Container (Interactive Mode)
Ensure that an X11 server is running and execute the following command to run the environment in interactive mode:

```
docker run -it --rm --name polyomino-env -p 10001:10001 -p 10002:10002 -e DISPLAY=host.docker.internal:0.0 polyomino-env:latest
```

Note: Running the environment under Git Bash also requires a pseudo-terminal emulator (e.g., winpty). For example,

```
winpty docker run -it --rm --name polyomino-env -p 10001:10001 -p 10002:10002 -e DISPLAY=host.docker.internal:0.0 polyomino-env:latest
```
