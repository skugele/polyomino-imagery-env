import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import zmq  # Python Bindings for ZeroMq (PyZMQ)
from PIL import Image  # Python Imaging Library

DEFAULT_TIMEOUT = 15000  # in milliseconds

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 10001

# by default, receives all published messages (i.e., all topics accepted)
MSG_TOPIC_FILTER = ''

IMAGE_DIRECTORY = Path('local/save/images')
IMAGE_DIMENSIONS = (128, 128)


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


def get_screenshot(viewport_data):
    return np.array(viewport_data['screenshot'])


def get_screenshot_filepath(viewport_data, extension):
    shape, id = viewport_data["shape"], viewport_data["id"]

    path = Path(f'{IMAGE_DIRECTORY}/{shape}/{id}')
    filename = f'polyomino_{extract_time(payload)}.{extension}'

    return path / filename


def save_screenshot(data, filepath):
    array = np.array(data, dtype=np.uint8)
    array = np.reshape(array, IMAGE_DIMENSIONS)

    img = Image.fromarray(array, mode='L')

    parent_dir = filepath.parent
    if not parent_dir.exists():
        print('creating path: ', str(parent_dir))
        parent_dir.mkdir(parents=True)

    img.save(filepath)


if __name__ == '__main__':
    try:
        args = parse_args()
        connection = connect(host=args.host, port=args.port)

        while True:
            topic, payload = receive(connection)

            if payload:
                viewport_data = payload['data']['right_viewport']

                filepath = get_screenshot_filepath(viewport_data, 'png')

                print('path: ', filepath)

                screenshot = get_screenshot(viewport_data)
                save_screenshot(screenshot, filepath)

                print(f'Image received: {payload["header"]}. Saved as {filepath}.', flush=True)

    except KeyboardInterrupt:

        try:
            sys.exit(1)
        except SystemExit:
            os._exit(1)
