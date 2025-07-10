import json
import sys
import threading
import time

import zmq

# blocking wait interval per attempt at receiving a message
RECEIVE_WAIT_MS = 1000  # in milliseconds

DEFAULT_HOST = "localhost"
DEFAULT_STATE_PORT = 10001
DEFAULT_ACTION_PORT = 10002

# script terminates if no message is received from the GAB state publisher within this time duration
DEFAULT_SHUTDOWN_TIMEOUT_MS = 25000  # in milliseconds

# by default, receives all published messages (i.e., all topics accepted)
SUB_ALL_TOPICS = ""

STATE_TOPIC = "/polyomino-world/state"
ACTION_REQ_TOPIC = "/polyomino/action_requested"

# used to signal the script to shutdown gracefully when a timer event or KeyboardInterrupt occurs
shutdown_event = threading.Event()


def get_state_subscriber(host=DEFAULT_HOST, port=DEFAULT_STATE_PORT, topic=SUB_ALL_TOPICS):
    """Establishes a connection to Godot AI Bridge state publisher.

    Args:
        host (str): The GAB state publisher's host IP address.
        port (int): The GAB state publisher's port number.
        topic (str): A message topic filter.

    Returns:
        zmq.Socket: The socket connection.
    """
    # creates a ZeroMQ subscriber socket
    socket = zmq.Context().socket(zmq.SUB)

    socket.setsockopt_string(zmq.SUBSCRIBE, topic)
    socket.setsockopt(zmq.RCVTIMEO, RECEIVE_WAIT_MS)

    socket.connect(f"tcp://{host}:{str(port)}")
    return socket


def get_action_publisher(host=DEFAULT_HOST, port=DEFAULT_ACTION_PORT):
    """Establishes a connection to the Godot AI Bridge action listener.

    Args:
        host (str): The IP address of the GAB action listener host.
        port (int): The port number of the GAB action listener.

    Returns:
        zmq.Socket: A ZeroMQ REQ socket connected to the action listener.
    """
    socket = zmq.Context().socket(zmq.REQ)
    socket.connect(f"tcp://{host}:{str(port)}")

    # without timeout the process can hang indefinitely
    socket.setsockopt(zmq.RCVTIMEO, RECEIVE_WAIT_MS)
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
    topic, encoded_payload = msg[0: ndx - 1], msg[ndx:]

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


def send(connection, request):
    """Sends an encoded request to the GAB action listener and returns its reply.
    Args:
        connection: A connection object to the GAB action listener.
        request (dict): A dictionary containing the action request payload.
    Returns:
        dict: The GAB action listener's reply, indicating SUCCESS or ERROR.
    """
    encoded_request = json.dumps(request)
    connection.send_string(encoded_request)

    reply = None
    try:
        reply = connection.recv_json()
    except zmq.Again:
        pass

    return reply


def create_action_request(data, seqno):
    """Creates a request payload for the GAB action listener.

    Args:
        data (dict): The action data to include in the request.
        seqno (int): The sequence number for the request.

    Returns:
        dict: The constructed request.
    """
    header = {
        "seqno": seqno,
        "time": round(time.time() * 1000),  # current time in milliseconds
    }

    return {"header": header, "data": data}


def add_verbose_arg(parser):
    """Adds a verbose argument to the parser."""
    parser.add_argument(
        "--verbose",
        action="store_true",
        required=False,
        help="enable verbose output",
    )


def add_timeout_arg(parser, default_timeout=DEFAULT_SHUTDOWN_TIMEOUT_MS):
    """Adds a timeout argument to the parser."""
    parser.add_argument(
        "--timeout",
        type=int,
        required=False,
        default=default_timeout,
        help=f"the maximum time in milliseconds to wait for a message before shutting down (default: {default_timeout} ms)",
    )


def add_port_arg(parser, default_port):
    """Adds a port argument to the parser."""
    parser.add_argument(
        "--port",
        type=int,
        required=False,
        default=default_port,
        help=f"the port number of the GAB state publisher (default: {default_port})",
    )


def add_host_arg(parser, default_host=DEFAULT_HOST):
    """Adds a host argument to the parser."""
    parser.add_argument(
        "--host",
        type=str,
        required=False,
        default=default_host,
        help=f"the IP address of host running the environment's state publisher (default: {default_host})",
    )
