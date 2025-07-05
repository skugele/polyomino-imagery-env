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
$ docker build -t polyomino-env:latest .
```

### Running Docker Container (Windows - Powershell)
Start a Windows compatible X11 server (e.g., VcXsrv or Xming) and run the
following command from the PowerShell terminal. (Powershell's prompt is shown as `PS> `.)

```
PS> docker run -it --rm --name polyomino-env -p 10001:10001 -p 10002:10002 -e DISPLAY=host.docker.internal:0.0 polyomino-env:latest
```

### Running Docker Container (Windows - Git Bash)
Git Bash additionally needs a pseudo-terminal emulator (e.g., winpty).

Start a Windows compatible X11 server (e.g., VcXsrv or Xming) and run the
following command from the Git Bash terminal. (Prompt shown as `$`.)

```
$ winpty docker run -it --rm --name polyomino-env -p 10001:10001 -p 10002:10002 -e DISPLAY=host.docker.internal:0.0 polyomino-env:latest
```
