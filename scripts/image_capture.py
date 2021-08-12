#
# Godot AI Bridge (GAB) - DEMO Environment State Listener.
#
# Description: Used to receive agent state information from DEMO environment via CLI
# Dependencies: PyZMQ (see https://pyzmq.readthedocs.io/en/latest/)
#

import json
import argparse
import sys
import os

import zmq  # Python Bindings for ZeroMq (PyZMQ)
import numpy as np

from PIL import Image  # Python Imaging Library

DEFAULT_TIMEOUT = 5000  # in milliseconds

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 10001

# by default, receives all published messages (i.e., all topics accepted)
MSG_TOPIC_FILTER = ''

IMAGES_DIRECTORY = 'D:/Data/polyomino-experiment/images'


def parse_args():
    """ Parses command line arguments. """
    parser = argparse.ArgumentParser(description='Godot AI Bridge (GAB) - DEMO Environment State Listener')

    parser.add_argument('--host', type=str, required=False, default=DEFAULT_HOST,
                        help=f'the IP address of host running the GAB state publisher (default: {DEFAULT_HOST})')
    parser.add_argument('--port', type=int, required=False, default=DEFAULT_PORT,
                        help=f'the port number of the GAB state publisher (default: {DEFAULT_PORT})')

    return parser.parse_args()


def connect(host=DEFAULT_HOST, port=DEFAULT_PORT):
    """ Establishes a connection to Godot AI Bridge state publisher.

    :param host: the GAB state publisher's host IP address
    :param port: the GAB state publisher's port number
    :return: socket connection
    """

    # creates a ZeroMQ subscriber socket
    socket = zmq.Context().socket(zmq.SUB)

    socket.setsockopt_string(zmq.SUBSCRIBE, MSG_TOPIC_FILTER)
    socket.setsockopt(zmq.RCVTIMEO, DEFAULT_TIMEOUT)

    socket.connect(f'tcp://{host}:{str(port)}')
    return socket


def receive(connection):
    """ Receives and decodes next message from the GAB state publisher, waiting until TIMEOUT reached in none available.

    :param connection: a connection to the GAB state publisher
    :return: a tuple containing the received message's topic and payload
    """
    msg = connection.recv_string()

    # messages are received as strings of the form: "<TOPIC> <JSON>". this splits the message string into TOPIC
    # and JSON-encoded payload
    ndx = msg.find('{')
    topic, encoded_payload = msg[0:ndx - 1], msg[ndx:]

    # unmarshal JSON message content
    payload = json.loads(encoded_payload)

    return topic, payload


def extract_time(payload):
    return payload['header']['time']


def get_screenshot(payload):
    screenshot = np.array(payload['data']['screenshot'])
    return screenshot

def get_screenshot_filename(payload, extension):
    return f'{IMAGES_DIRECTORY}/polyomino_{extract_time(payload)}.{extension}'

def save_screenshot(data, filename):
    array = np.array(data, dtype=np.uint8)
    array = np.reshape(array, (128, 128))

    img = Image.fromarray(array, mode='L')
    img.save(filename)


if __name__ == "__main__":
    try:
        args = parse_args()
        connection = connect(host=args.host, port=args.port)

        while True:
            topic, payload = receive(connection)

            screenshot = get_screenshot(payload)
            filename = get_screenshot_filename(payload, 'png')
            save_screenshot(screenshot, filename)

            print(f'Image received: {payload["header"]}. Saved as {filename}.', flush=True)

    except KeyboardInterrupt:

        try:
            sys.exit(1)
        except SystemExit:
            os._exit(1)
