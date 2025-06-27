from BVAE import BVAE
import tensorflow as tf
from sklearn.metrics.pairwise import cosine_similarity
import zmq, json, time
import numpy as np
import pandas as pd

path = "BVAE_Models/bvae_32dims_90acc.keras"
bvae_model = tf.keras.models.load_model(path, custom_objects = {'BVAE': BVAE})

context = zmq.Context()
listener = context.socket(zmq.SUB)
listener.setsockopt_string(zmq.SUBSCRIBE, "")
listener.setsockopt(zmq.RCVTIMEO, 50000)
listener.connect("tcp://localhost:10001")



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



while True:
    try:
        topic, payload = receive(listener)
        if "/state" in topic:
            left_viewport = payload["data"]["left_viewport"]["screenshot"]
            right_viewport = payload["data"]["right_viewport"]["screenshot"]

            left = tf.convert_to_tensor(left_viewport, dtype=tf.float32)
            right = tf.convert_to_tensor(right_viewport, dtype=tf.float32)
            left, right = tf.reshape(left, (128, 128, 1)), tf.reshape(right, (128, 128, 1))
            inputs = tf.stack([left, right], axis=0)  # Shape: (2, 128, 128, 1)
            mu, _, _, _ = bvae_model.encode(inputs)
            mu_left, mu_right = mu[0], mu[1]

            left_mean = left.numpy().mean(axis=(0, 1))
            right_mean = right.numpy().mean(axis=(0, 1))

            cosine_sim = cosine_similarity(mu_left.numpy().reshape(1, -1), mu_right.numpy().reshape(1, -1))[0][0]
            print(f"Cosine Similarity: {cosine_sim:.4f}, left mean: {left_mean}, right mean: {right_mean}")

            

    except Exception as e:
        print(f"An error occurred: {e}")
    time.sleep(0.1)  # Sleep to avoid busy waiting


