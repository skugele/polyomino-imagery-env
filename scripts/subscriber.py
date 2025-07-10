#
# Polyomino Imagery Environment State Listener
#
# Description: Used to receive agent state information from Polyomino Imagery Environment
# Dependencies: PyZMQ (see https://pyzmq.readthedocs.io/en/latest/)
#
import argparse
import os
import sys

from shared import DEFAULT_STATE_PORT
from shared import STATE_TOPIC
from shared import add_host_arg
from shared import add_port_arg
from shared import add_timeout_arg
from shared import add_verbose_arg
from shared import get_state_subscriber
from shared import receive
from shared import reset_shutdown_timer
from shared import shutdown_event


def parse_args():
    """Parses command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Polyomino Imagery Environment - State Listener"
    )

    add_host_arg(parser)
    add_port_arg(parser, default_port=DEFAULT_STATE_PORT)
    add_timeout_arg(parser)
    add_verbose_arg(parser)

    return parser.parse_args()


def main():
    """Main entry point for the script."""
    args = parse_args()
    connection = get_state_subscriber(
        host=args.host, port=args.port, topic=STATE_TOPIC)

    timer = reset_shutdown_timer(args.timeout)

    try:
        # Loop until timeout or keyboard interrupt
        while not shutdown_event.is_set():
            topic, payload = receive(connection)

            if payload:
                print(f"topic: {topic}; payload: {payload}", flush=True)
                timer = reset_shutdown_timer(args.timeout, timer)
            else:
                if args.verbose:
                    print("Waiting for messages...", flush=True)

    except KeyboardInterrupt:
        print("Interrupted by user. Shutting down...", flush=True)

    try:
        sys.exit(1)
    except SystemExit:
        os._exit(1)


if __name__ == "__main__":
    main()
