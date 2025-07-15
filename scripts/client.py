#
# Polyomino Imagery Environment Action Client
#
# Description: Used to submit commands (actions) to the Polyomino Imagery Environment
# Dependencies: PyZMQ (see https://pyzmq.readthedocs.io/en/latest/)
#
import argparse
import os
import platform
import sys

from shared import DEFAULT_ACTION_PORT
from shared import add_host_arg
from shared import add_port_arg
from shared import add_verbose_arg
from shared import create_action_request
from shared import get_action_publisher
from shared import send

# maps single character user inputs from command line to Godot agent actions
ACTION_MAP = {
    "W": "up",
    "S": "down",
    "A": "left",
    "D": "right",
    "Q": "rotate_counterclockwise",
    "E": "rotate_clockwise",
    "+": "zoom_in",
    "-": "zoom_out",
    "N": "next_shape",
    "1": "select_same_shape",
    "0": "select_different_shape",
}

ACTION_IDS = list(ACTION_MAP.keys())


def parse_args():
    """Parses command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Polyomino Imagery Environment - Action Client"
    )

    add_host_arg(parser)
    add_port_arg(parser, default_port=DEFAULT_ACTION_PORT)
    add_verbose_arg(parser)

    return parser.parse_args()


def is_git_bash():
    """Checks if the script is running in Git Bash on Windows."""
    shell = os.environ.get("SHELL", "")
    term = os.environ.get("TERM", "")

    return (
            "mintty" in term.lower()
            or "msys" in shell.lower()
            or "git" in shell.lower()
            or "mingw" in term.lower()
    )


def get_action_from_user(platform_id=None):
    """Reads a single keypress from the user
    - On Windows: returns the key immediately.
    - On Linux/macOS: returns the key immediately.
    - On other platforms: falls back to requiring Enter.
    """

    # must exclude Git Bash on Windows because it doesn't work with msvcrt
    if platform_id == "Windows" and not is_git_bash():
        import msvcrt
        action = msvcrt.getwch()

    elif platform_id in ("Linux", "Darwin"):  # Darwin = macOS
        import tty
        import termios

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            action = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    else:
        # unsupported platform: enter must be pressed
        action = input("Enter a command (then press Enter): ")

    return action.upper()


def get_prompt(platform_id=None):
    supported_platforms = ("Windows", "Linux", "Darwin")  # Darwin = macOS

    # prompt for supported platforms that allow action input without hitting Enter
    default_prompt = f'Select an action ({", ".join(ACTION_IDS[0:-1])}, or {ACTION_IDS[-1]})'

    # prompt for non-supported platforms that require Enter following each action
    alt_prompt = f'{default_prompt} followed by [ENTER]'

    return default_prompt if platform_id in supported_platforms else alt_prompt


def main():
    """Main entry point for the script."""
    try:
        args = parse_args()

        platform_id = platform.system()
        if args.verbose:
            print(f"Detected platform: {platform_id}", flush=True)

        prompt = get_prompt(platform_id)

        connection = get_action_publisher(host=args.host, port=args.port)
        seqno = 1  # current request's sequence number

        # MAIN LOOP: receive action via CLI, and send it to GAB action listener
        while True:
            print(prompt, flush=True)
            action = get_action_from_user(platform_id)  # read a single keypress
            if action not in ACTION_MAP:
                break

            if args.verbose:
                print(f'You selected {action}')

            request = create_action_request(
                data={"event": {"type": "action", "value": ACTION_MAP[action]}},
                seqno=seqno,
            )

            reply = send(connection, request)

            if args.verbose:
                print(f"\t REQUEST: {request}")
                print(f"\t REPLY: {reply}")

            seqno += 1

    except KeyboardInterrupt:
        print("Interrupted by user. Shutting down...", flush=True)

    try:
        sys.exit(1)
    except SystemExit:
        os._exit(1)


if __name__ == "__main__":
    main()
