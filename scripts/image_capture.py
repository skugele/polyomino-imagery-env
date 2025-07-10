import argparse
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image

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

# Directory where images will be saved
DEFAULT_SAVE_PATH = Path('local/save/images')

IMAGE_DIMENSIONS = (128, 128)


def parse_args():
    """ Parses command line arguments. """
    parser = argparse.ArgumentParser(
        description='Polyomino Imagery Environment - State to Image Exporter')

    add_host_arg(parser)
    add_port_arg(parser, default_port=DEFAULT_STATE_PORT)
    add_verbose_arg(parser)
    add_timeout_arg(parser)

    parser.add_argument(
        "--savepath",
        type=Path,
        required=False,
        help=f"Path to the directory where images will be saved (default: '{DEFAULT_SAVE_PATH}').",
        default=DEFAULT_SAVE_PATH
    )

    return parser.parse_args()


def extract_time(payload):
    return payload['header']['time']


def get_screenshot(viewport_data):
    return np.array(viewport_data['screenshot'])


def get_screenshot_filepath(basedir, payload, viewport_data, extension):
    path = Path(f'{basedir}/{viewport_data["shape"]}')
    filename = f'polyomino_{extract_time(payload)}.{extension}'

    return path / filename


def save_screenshot(data, filepath):
    array = np.array(data, dtype=np.uint8)
    array = np.reshape(array, IMAGE_DIMENSIONS)

    img = Image.fromarray(array, mode='L')

    parent_dir = filepath.parent
    if not parent_dir.exists():
        print('creating path: ', str(parent_dir), flush=True)
        parent_dir.mkdir(parents=True)

    img.save(filepath)


def main():
    """ Main entry point for the script. """
    try:
        args = parse_args()
        connection = get_state_subscriber(
            host=args.host, port=args.port, topic=STATE_TOPIC)

        timer = reset_shutdown_timer(args.timeout)

        # Loop until timeout or keyboard interrupt
        while not shutdown_event.is_set():
            topic, payload = receive(connection)

            if payload:
                print(f"topic: {topic}; payload: {payload}", flush=True)
                viewport_data = payload['data']['right_viewport']
                filepath = get_screenshot_filepath(
                    args.savepath, payload, viewport_data, 'png')

                screenshot = get_screenshot(viewport_data)
                save_screenshot(screenshot, filepath)

                timer = reset_shutdown_timer(args.timeout, timer)

                if args.verbose:
                    print(f'Image received: {payload["header"]}. Saved as {filepath}.', flush=True)
            else:
                if args.verbose:
                    print("Waiting for messages...", flush=True)

    except KeyboardInterrupt:
        print("Interrupted by user. Shutting down...", flush=True)

    try:
        sys.exit(1)
    except SystemExit:
        os._exit(1)


if __name__ == '__main__':
    main()
