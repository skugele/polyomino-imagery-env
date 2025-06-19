import gymnasium as gym
import zmq, json, time
from enum import Enum
from itertools import cycle
import numpy as np
import tensorflow as tf
import pandas as pd
from BVAE import BVAE

latent_dimensions = 16
bvae_model = None

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
    def __init__(self, PORT = 10002, LISTENER_PORT = 10001, HOST = 'localhost', TIMEOUT = 5000, MSG_TIMEOUT_FILTER = '', MAX_TIMESTEPS = 1000):
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


    def _send(self, data):
        self.seqno += 1
        request = self._create_request(data)
        encoded_req = json.dumps(request)
        self.socket.send_string(encoded_req)
        self._wait_for_update(self.seqno)
        return self.socket.recv_json()
    
    def _recv(self):
        msg = self.listener.recv_string()

        ndx = msg.find('{')
        topic, encoded_payload = msg[0:ndx - 1], msg[ndx:]

        # unmarshal JSON message content
        payload = json.loads(encoded_payload)

        return topic, payload
        

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
                reward = -1
            else:
                isCorrect = self._check_selection(action == Actions.SELECT_SAME.value)
                reward = 10 if isCorrect else -20
            self.answered = True
        else:
            reward = -1

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
        left = tf.convert_to_tensor(left, dtype=tf.float32)
        right = tf.convert_to_tensor(right, dtype=tf.float32)
        left, right = tf.reshape(left, (128, 128, 1)), tf.reshape(right, (128, 128, 1))
        inputs = tf.stack([left, right], axis=0)  # Shape: (2, 128, 128, 1)
        mu, _, _, _ = bvae_model.encode(inputs)
        mu_left, mu_right = mu[0], mu[1]

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
        left = tf.convert_to_tensor(left, dtype=tf.float32)
        right = tf.convert_to_tensor(right, dtype=tf.float32)
        left, right = tf.reshape(left, (128, 128, 1)), tf.reshape(right, (128, 128, 1))
        inputs = tf.stack([left, right], axis=0)  # Shape: (2, 128, 128, 1)
        mu, _, _, _ = bvae_model.encode(inputs)
        mu_left, mu_right = mu[0], mu[1]

        observation = {
            "left": mu_left.numpy(),
            "right": mu_right.numpy(),
        }

        info = response
        # terminated = self.MAX_TIMESTEPS <= self.current_timestep;
        terminated = self.MAX_PROBLEMS <= self.current_problem
        truncated = False
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

from stable_baselines3 import PPO, DQN
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import CheckpointCallback

def train_model(training_model, training_steps = 100000, buffer_size = 30000, load_model = None):
    global bvae_model
    bvae_path = "./bvae_model_ldims_16_1750247228_new.keras"
    bvae_model = tf.keras.models.load_model(bvae_path, custom_objects = {'BVAE': BVAE})
    print(bvae_model.summary())
    print("Setting latent dimensions", bvae_model.latent_dims)


    print("Testing with ", training_model.__name__, "for", training_steps, "steps")

    env = PolyominoEnvironment()
    env = Monitor(env)
    checkpoint_callback = CheckpointCallback(
        save_freq=10000,
        save_path=f"./models/",
        name_prefix=f"{training_model.__name__}_{training_steps}"
    )
    # model = PPO.load("./model-PPO-300000.zip")
    check_env(env, warn=True)

    if load_model:
        model = training_model.load(load_model, env=env, verbose=1)
    else:
        if training_model.__name__ == "DQN":
            model = training_model("MultiInputPolicy", env, verbose=1, buffer_size=buffer_size, tensorboard_log="./tensorboard_logs/")


    model.learn(total_timesteps=training_steps, callback=checkpoint_callback)
    model.save(f"model-{training_model.__name__}-{training_steps}")

    obs, info = env.reset()
    while True:
        action, _ = model.predict(obs)
        print(action)
        obs, reward, term, trun, info = env.step(action)
        print(reward)
        # print(action, reward)
        input()
        if term or trun:
            obs = env.reset()
            break

def get_latest_model():
    model_dir = "./models/"
    import os

    files = [f for f in os.listdir(model_dir) if f.endswith('.zip')]
    # sort them and get the latest one
    files.sort(key=lambda x: os.path.getmtime(os.path.join(model_dir, x)), reverse=True)
    if files:
        return os.path.join(model_dir, files[0])
    else:
        return None


if __name__ == "__main__":
    latest_model_path = None

    # latest_model_path = get_latest_model()
    # print(latest_model_path)

    train_model(DQN, training_steps=500000, load_model=latest_model_path)
