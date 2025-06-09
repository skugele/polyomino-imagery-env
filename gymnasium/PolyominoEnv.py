import gymnasium as gym
import zmq, json, time
from enum import Enum
from itertools import cycle
import numpy as np

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

        self.MAX_TIMESTEPS = MAX_TIMESTEPS;
        self.current_timestep = 0;

        self.SELECTION_ACTIONS = [Actions.SELECT_SAME.value, Actions.SELECT_DIFFERENT.value]

        self.seqno = 1

        self.latest_env_state = None

        self.observation_space = gym.spaces.Dict({
            "left": gym.spaces.Box(low=0, high=255, shape=(16384,), dtype=np.float32),
            "right": gym.spaces.Box(low=0, high=255, shape=(16384,), dtype=np.float32),
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

        left, right = self.latest_env_state["state"]
        print(len(left), len(right))

        left = np.array(left, dtype=np.float32)
        right = np.array(right, dtype=np.float32)
        observation = {
            "left": left,
            "right": right
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



        if action in self.SELECTION_ACTIONS:
            isCorrect = self._check_selection(action == Actions.SELECT_SAME.value)
            reward = 10 if isCorrect else -10
        else:
            reward = -1  # or 0 depending on neutrality of non-selection moves
 

        left, right = self.latest_env_state["state"]

        left = np.array(left, dtype=np.float32)
        right = np.array(right, dtype=np.float32)
        observation = {
            "left": left,
            "right": right
        }      

        info = response
        terminated = self.MAX_TIMESTEPS <= self.current_timestep;
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
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.monitor import Monitor

def main():
    env = PolyominoEnvironment()
    env = Monitor(env)
    check_env(env, warn=True)

    model = PPO("MultiInputPolicy", env, verbose=1)
    model.learn(total_timesteps=1000000)

    obs, info = env.reset()
    while True:
        action, _ = model.predict(obs)
        obs, reward, term, trun, info = env.step(action)
        print(action, reward)
        if term or trun:
            obs = env.reset()
            break

if __name__ == "__main__":
    main()
