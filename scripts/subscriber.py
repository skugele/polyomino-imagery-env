#
# Polyomino Imagery Environment State Listener
#
# Description: Used to receive agent state information from Polyomino Imagery Environment
# Dependencies: PyZMQ (see https://pyzmq.readthedocs.io/en/latest/)
#

import argparse
import json
import sys
import threading

import zmq  # Python Bindings for ZeroMq (PyZMQ)

# script terminates if no message is received from the GAB state publisher within this time duration
DEFAULT_SHUTDOWN_TIMEOUT_MS = 25000  # in milliseconds

# blocking wait interval per attempt at receiving a message
RECEIVE_WAIT_MS = 1000  # in milliseconds

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 10001

# by default, receives all published messages (i.e., all topics accepted)
MSG_TOPIC_FILTER = ""

# used to signal the script to shutdown gracefully when a timer event or KeyboardInterrupt occurs
shutdown_event = threading.Event()


def parse_args():
    """Parses command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Polyomino Imagery Environment State Listener"
    )

    parser.add_argument(
        "--host",
        type=str,
        required=False,
        default=DEFAULT_HOST,
        help=f"the IP address of host running the environment's state publisher (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        required=False,
        default=DEFAULT_PORT,
        help=f"the port number of the GAB state publisher (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        required=False,
        default=DEFAULT_SHUTDOWN_TIMEOUT_MS,
        help=f"the maximum time in milliseconds to wait for a message before shutting down (default: {DEFAULT_SHUTDOWN_TIMEOUT_MS} ms)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        required=False,
        help="enable verbose output (default: False)",
    )

    return parser.parse_args()


def connect(host=DEFAULT_HOST, port=DEFAULT_PORT):
    """Establishes a connection to Godot AI Bridge state publisher.

    Args:
        host (str): The GAB state publisher's host IP address.
        port (int): The GAB state publisher's port number.

    Returns:
        zmq.Socket: The socket connection.
    """
    # creates a ZeroMQ subscriber socket
    socket = zmq.Context().socket(zmq.SUB)

    socket.setsockopt_string(zmq.SUBSCRIBE, MSG_TOPIC_FILTER)
    socket.setsockopt(zmq.RCVTIMEO, RECEIVE_WAIT_MS)

    socket.connect(f"tcp://{host}:{str(port)}")
    return socket


def receive(connection):
    """Receives and decodes next message from the GAB state publisher, waiting until TIMEOUT reached if none available.

    Args:
        connection (zmq.Socket): A connection to the GAB state publisher.

    Returns:
        tuple: A tuple containing the received message's topic (str) and payload (dict or None).
    """
    try:
        msg = connection.recv_string()
    except zmq.Again:
        # if no message is received within the RECEIVE_WAIT_MS timeout, return None
        return None, None

    # messages are received as strings of the form: "<TOPIC> <JSON>". this splits the message string into TOPIC
    # and JSON-encoded payload
    ndx = msg.find("{")
    topic, encoded_payload = msg[0 : ndx - 1], msg[ndx:]

    # unmarshal JSON message content
    payload = json.loads(encoded_payload)

    return topic, payload


def reset_shutdown_timer(timeout, timer=None):
    """Starts or resets the shutdown timer.

    Args:
        timeout (int): The maximum time in milliseconds to wait for a message before shutting down.
        timer (threading.Timer, optional): The existing timer to reset. Defaults to None.

    Returns:
        threading.Timer: The reset or newly created timer instance.
    """
    if timer and timer.is_alive():
        timer.cancel()

    def timeout_handler():
        print(
            f"No message received for {timeout / 1000.0} seconds. Shutting down...",
            file=sys.stderr,
        )
        shutdown_event.set()

    timer = threading.Timer(timeout / 1000.0, timeout_handler)
    timer.start()

    return timer


def main():
    """Main entry point for the script."""
    args = parse_args()
    connection = connect(host=args.host, port=args.port)

    timer = reset_shutdown_timer(args.timeout)

    try:
        # Loop until timeout or keyboard interrupt
        while not shutdown_event.is_set():
            topic, payload = receive(connection)

            if payload is not None:
                print(f"topic: {topic}; payload: {payload}", flush=True)
                timer = reset_shutdown_timer(args.timeout, timer)
            else:
                if args.verbose:
                    print("Waiting for messages...", flush=True)

    except KeyboardInterrupt:
        print("Interrupted by user. Shutting down...")


if __name__ == "__main__":
    main()
