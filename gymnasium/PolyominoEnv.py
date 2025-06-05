import gym
import zmq, json, time
from enum import Enum

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
    def __init__(self, PORT = 10002, LISTENER_PORT = 10001, HOST = 'localhost', TIMEOUT = '5000', MSG_TIMEOUT_FILTER = ''):
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

        self.seqno = 1

        self.latest_reward = None
        self.latest_env_state = None

        self._connect()
        self._listener_connect()


    def _connect(self):
        self.socket = zmq.Context().socket(zmq.REQ)
        self.socket.connect(f"tcp://{self.HOST}:{str(self.PORT)}")
        self.socket.setsocketopt(zmq.RCVTIMEO, self.TIMEOUT)

    def _listener_connect(self):
        self.listener = zmq.Context().socket(zmq.SUB)
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
        request = self._create_request(data)
        encoded_req = json.dumps(request)
        self.socket.send_string(encoded_req)
        return self.socket.recv_json()
    
    def _recv(self):
        msg = self.listener.recv_string()

        ndx = msg.find('{')
        topic, encoded_payload = msg[0:ndx - 1], msg[ndx:]

        # unmarshal JSON message content
        payload = json.loads(encoded_payload)

        return topic, payload
        
    def _wait_for_reward(self, timeout_ms = 1000):
        end_time = time.time() + (timeout_ms / 1000)
        while time.time() < end_time:
            topic, payload = self._recv()
            if "result" in topic:
                return 1 if payload["result"] else -1
        return 0

    def _get_environment_state(self, timeout_ms = 1000):
        end_time = time.time() + (timeout_ms / 1000)
        while time.time() < end_time:
            pass

    def _process_listener_msgs(self, timeout_ms = 1000):
        end_time = time.time() + (timeout_ms / 1000)
        while time.time() < end_time: 
            pass
            topic, payload = self._recv()
            if "result" in topic:
                self.latest_reward = 1 if payload["result"] else -1
            elif "state" in topic:
                self.latest_env_state = payload["data"]["screenshot"]



    def reset(self):
        super().reset()
        data = {
            'event': {
                'type': 'action',
                'value': self.ACTION_DESC[Actions.NEXT_SHAPE.value]
            }
        }
        self._send(data)

    def step(self, action):
        data = {
            'event': {
                'type': 'action',
                'value': self.ACTION_DESC[action]
            }
        }
        response = self._send(data)
        assert(response['data']['status']=='SUCCESS')

        # wait for the responses
        self._process_listener_msgs()

        # terminated? what is the terminated state? when has the agent reached its goal

        assert(self.latest_reward is not None and self.latest_env_state is not None)


        reward = self.latest_reward if action in [Actions.SELECT_SAME, Actions.SELECT_DIFFERENT] else 0

        observation = response
        info = response
        terminated = False
        truncated = False

        return observation, reward, terminated, truncated, info




    def close(self):
        pass


"""
environment_state: pixel data (screenshot)

are the actions hidden to the agent based on the playMode?


different approach to listener msgs.
"""
