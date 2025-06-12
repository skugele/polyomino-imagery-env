import gymnasium as gym
import zmq, json, time
from enum import Enum
from itertools import cycle
import numpy as np
import tensorflow as tf
import pandas as pd

from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
import torch
import torch.nn as nn

class CustomCNNExtractor(BaseFeaturesExtractor):
    def __init__(self, observation_space, features_dim=256):
        super(CustomCNNExtractor, self).__init__(observation_space, features_dim)
        
        # CNN for processing images (assuming 128x128 grayscale images)
        self.cnn = nn.Sequential(
            nn.Conv2d(2, 32, kernel_size=3, padding=1),  # 2 channels for left+right
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, padding=1), 
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((8, 8)),  # Reduce spatial dimensions
            nn.Flatten()
        )
        
        # Calculate CNN output size
        cnn_output_size = 64 * 8 * 8  # 4096
        
        # Dense layers
        self.fc = nn.Sequential(
            nn.Linear(cnn_output_size + 2, 256),  # +2 for discrete features
            nn.ReLU(),
            nn.Linear(256, features_dim),
            nn.ReLU()
        )
    
    def forward(self, observations):
        # Reshape pixel arrays to images (assuming 128x128)
        left = observations['left'].view(-1, 1, 128, 128)
        right = observations['right'].view(-1, 1, 128, 128)
        
        # Concatenate as 2-channel image
        images = torch.cat([left, right], dim=1)
        
        # Process through CNN
        cnn_features = self.cnn(images)  # Shape: [batch_size, 4096]
        
        # Get discrete features and ensure proper shape
        last_action = observations['last_action_selection']
        answered_correct = observations['answered_correct']
        
        # Handle different input shapes (squeeze extra dimensions if needed)
        if last_action.dim() > 1:
            last_action = last_action.squeeze(-1)
        if answered_correct.dim() > 1:
            answered_correct = answered_correct.squeeze(-1)
            
        discrete_features = torch.stack([
            last_action.float(),
            answered_correct.float()
        ], dim=-1)  # Shape: [batch_size, 2]
        
        # Combine features (both should be 2D now)
        combined = torch.cat([cnn_features, discrete_features], dim=-1)
        
        return self.fc(combined)
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

        self.answered_correct = False
        self.last_action_selection = False

        # self.observation_space = gym.spaces.Dict({
        #     "left": gym.spaces.Box(low=0, high=255, shape=(16384,), dtype=np.float32),
        #     "right": gym.spaces.Box(low=0, high=255, shape=(16384,), dtype=np.float32),
        #     "last_action_selection": gym.spaces.Discrete(2),
        #     "answered_correct": gym.spaces.Discrete(2)

        # })
        self.observation_space = gym.spaces.Dict({
            "left": gym.spaces.Box(low=0, high=255, shape=(16384,), dtype=np.float32),
            "right": gym.spaces.Box(low=0, high=255, shape=(16384,), dtype=np.float32),
            "last_action_selection": gym.spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32),
            "answered_correct": gym.spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32)
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
            topic, payload = self._recv()
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
        # print(len(left), len(right))

        self.answered_correct = False
        self.last_action_selection = False

        left = np.array(left, dtype=np.float32)
        right = np.array(right, dtype=np.float32)
        # observation = {
        #     "left": left,
        #     "right": right,
        #     "last_action_selection": 0,
        #     "answered_correct": 0
        # }
        observation = {
            "left": left,
            "right": right,
            "last_action_selection": np.array([0], dtype=np.float32),
            "answered_correct": np.array([0], dtype=np.float32)
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

        # wait for the responses

        # terminated? what is the terminated state? when has the agent reached its goal


        # print(self.latest_env_state)


        # if self.answered_correct:
        #     if action != Actions.NEXT_SHAPE.value:
        #         reward = -10
        #     else:
        #         reward = 10 
        # elif action == Actions.NEXT_SHAPE.value:
        #         reward = -25
        # else:
        #     if action in self.SELECTION_ACTIONS:
        #         isCorrect = self._check_selection(action == Actions.SELECT_SAME.value)
        #         if isCorrect:
        #             reward = 10
        #         else:
        #             reward = -20
        #     else:
        #         reward = -1 

        # promote trying different configurations to generalize better, todo
        if action in self.SELECTION_ACTIONS:
            if self.answered_correct:
                reward = -25
            elif self.last_action_selection:
                reward = -10
            else:
                isCorrect = self._check_selection(action == Actions.SELECT_SAME.value)
                if isCorrect:
                    self.answered_correct = True
                reward = 35 if isCorrect else -50
        else:
            reward = -1

        if action == Actions.NEXT_SHAPE.value:
            reward = 30 if self.answered_correct else -55


     
        if action in self.SELECTION_ACTIONS:
            self.last_action_selection = True
        else:
            self.last_action_selection = False

        if action == Actions.NEXT_SHAPE.value:
            self.current_problem += 1
            self.answered_correct = False # reset after choosing the next shape

        left, right = self.latest_env_state["state"]

        left = np.array(left, dtype=np.float32)
        right = np.array(right, dtype=np.float32)
        # observation = {
        #     "left": left,
        #     "right": right,
        #     "last_action_selection": 1 if self.last_action_selection else 0,
        #     "answered_correct": 1 if self.answered_correct else 0
        # }      
        observation = {
            "left": left,
            "right": right,
            "last_action_selection": np.array([1 if self.last_action_selection else 0], dtype=np.float32),
            "answered_correct": np.array([1 if self.answered_correct else 0], dtype=np.float32)
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

#
# def main():
#     env = PolyominoEnvironment()
#     actions = [8, 0, 9]
#     actions = cycle(actions)
#     while True:
#         action = next(actions)
#         obs, reward, term, trun, info =  env.step(action)
#         print(action, reward)
#         time.sleep(2)
#
from stable_baselines3 import PPO, DQN
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import CheckpointCallback

def train_model(training_model, training_steps = 100000, buffer_size = 30000, load_model = None):
    print("Testing with ", training_model.__name__, "for", training_steps, "steps")

    policy_kwargs = dict(
        features_extractor_class=CustomCNNExtractor,  # This IS your CNN
        features_extractor_kwargs=dict(features_dim=256),
    )
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
            model = training_model("MultiInputPolicy", env, verbose=1, buffer_size=buffer_size, tensorboard_log="./tensorboard_logs/", policy_kwargs=policy_kwargs)
        elif training_model.__name__ == "PPO":
            model = training_model("MultiInputPolicy", env, verbose=1, ent_coef=0.001, tensorboard_log="./tensorboard_logs/")

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
