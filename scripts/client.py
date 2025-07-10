#
# Polyomino Imagery Environment Action Client
#
# Description: Used to submit commands (actions) to the Polyomino Imagery Environment
# Dependencies: PyZMQ (see https://pyzmq.readthedocs.io/en/latest/)
#
import argparse
import os
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


def main():
    """Main entry point for the script."""
    try:
        args = parse_args()
        connection = get_action_publisher(host=args.host, port=args.port)

        seqno = 1  # current request's sequence number

        # MAIN LOOP: receive action via CLI, and send it to GAB action listener
        print("Select an action ID followed by [ENTER]. (All other keys quit.)")
        while True:
            # displays available action ids on each prompt
            action = input(
                f'>> {", ".join(ACTION_IDS[0:-1])}, or {ACTION_IDS[-1]}? '
            ).upper()

            if action not in ACTION_MAP:
                break

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
