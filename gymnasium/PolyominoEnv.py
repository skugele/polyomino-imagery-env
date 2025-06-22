import gymnasium as gym
import zmq, json, time
from enum import Enum
from itertools import cycle
import numpy as np
import tensorflow as tf
import pandas as pd
from BVAE import BVAE
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='polyomino_env.log', filemode='a')
logging.info("============== Polyomino Environment initialized ================")

class Actions(Enum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    ROTATE_COUNTERCLOCKWISE = 4
    ROTATE_CLOCKWISE = 5
    ZOOM_IN = 6
    ZOOM_OUT = 7
    NEXT_SHAPE = 8
    SELECT_SAME = 9
    SELECT_DIFFERENT = 10

class PolyominoEnvironment(gym.Env):
    def __init__(self, PORT = 10002, LISTENER_PORT = 10001, HOST = 'localhost', TIMEOUT = 5000, MSG_TIMEOUT_FILTER = '', MAX_TIMESTEPS = 1000, BVAE_MODEL_PATH = "./bvae_model_ldims_16_1750247228_new.keras"):
        self.ACTION_MAP = {
              'W': 'up',
              'S': 'down',
              'A': 'left',
              'D': 'right',
              'Q': 'rotate_counterclockwise',
              'E': 'rotate_clockwise',
              '+': 'zoom_in',
              '_': 'zoom_out',
              'N': 'next_shape',
              '1': 'select_same_shape',
              '0': 'select_different_shape'
        }

        self.bvae_model = self._load_bvae(BVAE_MODEL_PATH)

        self.ACTION_KEYS = list(self.ACTION_MAP.keys())
        self.ACTION_DESC = list(self.ACTION_MAP.values())
        self.action_space = gym.spaces.Discrete(len(self.ACTION_KEYS))

        self.PORT = PORT
        self.LISTENER_PORT = LISTENER_PORT
        self.HOST = HOST
        self.TIMEOUT = TIMEOUT
        self.MSG_TOPIC_FILTER = MSG_TIMEOUT_FILTER

        self.MAX_TIMESTEPS = MAX_TIMESTEPS
        self.current_timestep = 0

        self.MAX_PROBLEMS = 50
        self.current_problem = 0

        self.SELECTION_ACTIONS = [Actions.SELECT_SAME.value, Actions.SELECT_DIFFERENT.value]

        self.seqno = 1

        self.latest_env_state = None

        self.answered = False

        latent_dimensions = self.bvae_model.latent_dims
        self.observation_space = gym.spaces.Dict({
            "left": gym.spaces.Box(low=-np.inf, high=np.inf, shape=(latent_dimensions,), dtype=np.float32),
            "right": gym.spaces.Box(low=-np.inf, high=np.inf, shape=(latent_dimensions,), dtype=np.float32),
        })

        self.context = zmq.Context()
        self._connect()
        self._listener_connect()


    def _connect(self):
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(f"tcp://{self.HOST}:{self.PORT}")
        self.socket.setsockopt(zmq.RCVTIMEO, self.TIMEOUT)

    def _listener_connect(self):
        self.listener = self.context.socket(zmq.SUB)
        self.listener.setsockopt_string(zmq.SUBSCRIBE, self.MSG_TOPIC_FILTER)
        self.listener.setsockopt(zmq.RCVTIMEO, self.TIMEOUT)
        self.listener.connect(f"tcp://{self.HOST}:{str(self.LISTENER_PORT)}")

    def _create_request(self, data):
        header = {
            'seqno': self.seqno,
            'time': round(time.time() * 1000) # milliseconds
        }

        return {'header': header, 'data': data}


    def _load_bvae(self, path):
        bvae_model = tf.keras.models.load_model(path, custom_objects = {'BVAE': BVAE})
        print(f"Loading Model with latent dimensions {bvae_model.latent_dims}")
        print(bvae_model.summary())
        return bvae_model

    def _send(self, data):
        self.seqno += 1
        request = self._create_request(data)
        encoded_req = json.dumps(request)
        self.socket.send_string(encoded_req)
        self._wait_for_update(self.seqno)

        while True:
            try:
                return self.socket.recv_json(flags=zmq.NOBLOCK)
            except zmq.Again:
                continue
    

    def _recv(self):
        while True:
            try:
                msg = self.listener.recv_string(flags=zmq.NOBLOCK)
                break
            except zmq.Again:
                continue

        ndx = msg.find('{')
        topic, encoded_payload = msg[0:ndx - 1], msg[ndx:]
        payload = json.loads(encoded_payload)
        return topic, payload
    
    def _encode_state(self, left, right):
        left = tf.convert_to_tensor(left, dtype=tf.float32)
        right = tf.convert_to_tensor(right, dtype=tf.float32)
        left, right = tf.reshape(left, (128, 128, 1)), tf.reshape(right, (128, 128, 1))
        inputs = tf.stack([left, right], axis=0)  # Shape: (2, 128, 128, 1)
        mu, _, _, _ = self.bvae_model.encode(inputs)
        mu_left, mu_right = mu[0], mu[1]
        return mu_left, mu_right

    def _wait_for_update(self, seqNo, timeout_ms=5000):
        end_time = time.time() + (timeout_ms / 1000)

        while time.time() < end_time:
            try:
                topic, payload = self._recv()
            except zmq.Again:
                continue
            # print(topic, payload)
            if "/state" in topic:
                lastActionSeqNo = payload["data"]["last_action_seqno"]
                if lastActionSeqNo >= seqNo:
                    self.latest_env_state = {
                        'state': [payload['data']['left_viewport']['screenshot'], payload['data']['right_viewport']['screenshot']],
                        'isSame': payload['data']['same']
                    }
                    return


    def _check_selection(self, selected_same):
        return self.latest_env_state["isSame"] == selected_same
    
    def calculate_reward(self, action):
        #simplified for test
        if action in self.SELECTION_ACTIONS:
            if self.answered:
                reward = -0.05
            else:
                isCorrect = self._check_selection(action == Actions.SELECT_SAME.value)
                reward = 1 if isCorrect else -1
            self.answered = True
        else:
            if action == Actions.NEXT_SHAPE.value and not self.answered:
                reward = -1
            else:
                reward = -0.05

        return reward

    def reset(self, seed=42):
        data = {
            'event': {
                'type': 'action',
                'value': self.ACTION_DESC[Actions.NEXT_SHAPE.value]
            }
        }
        self._send(data)
        self.current_timestep = 0
        self.current_problem = 0

        left, right = self.latest_env_state["state"]
        mu_left, mu_right = self._encode_state(left, right)

        self.answered= False

        observation = {
            "left": mu_left.numpy(),
            "right": mu_right.numpy(),
        }

        info = {}
        return (observation, info)

    def step(self, action):
        self.current_timestep += 1
        data = {
            'event': {
                'type': 'action',
                'value': self.ACTION_DESC[action]
            }
        }
        response = self._send(data)
        assert(response['data']['status']=='SUCCESS')

        reward = self.calculate_reward(action)

        if action == Actions.NEXT_SHAPE.value:
            self.current_problem += 1
            self.answered= False # reset after choosing the next shape

        left, right = self.latest_env_state["state"]
        mu_left, mu_right = self._encode_state(left, right)

        observation = {
            "left": mu_left.numpy(),
            "right": mu_right.numpy(),
        }

        info = response
        # terminated = self.MAX_TIMESTEPS <= self.current_timestep;
        terminated = self.MAX_PROBLEMS <= self.current_problem
        truncated = False
        logging.info(f"Observation: {observation}, Action: {action}, Reward: {reward}, Terminated: {terminated}, Truncated: {truncated}, Info: {info}")
        return observation, reward, terminated, truncated, info

    def close(self):
        self.socket.close()
        self.listener.close()
        self.context.term()


"""
environment_state: pixel data (screenshot)

are the actions hidden to the agent based on the playMode?; currently agent can send the actions but if the env is not in playMode nothing will change


different approach to listener msgs.: use sqn no to sync the data
"""

