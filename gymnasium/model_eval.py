from PolyominoEnv import PolyominoEnvironment
from stable_baselines3 import PPO, DQN
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import CheckpointCallback
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

def eval(model_path, no_of_episodes=25):
    CORRECT_ANSWER_REWARD = 1
    WRONG_ANSWER_PENALTY = -1

    env = PolyominoEnvironment()
    env = Monitor(env)
    model = PPO.load(model_path, exploration_initial_eps=0)

    check_env(env, warn=True)

    obs, _ = env.reset()
    total_reward = 0
    correct = wrong = 0
    while no_of_episodes > 0:
        action, _ = model.predict(obs)
        obs, reward, term, trun, _ = env.step(action)
        total_reward += reward

        if reward == CORRECT_ANSWER_REWARD:
            correct += 1
        elif reward == WRONG_ANSWER_PENALTY:
            wrong += 1

        if term or trun:
            obs, _ = env.reset()
            break
        if action == Actions.NEXT_SHAPE.value:
            no_of_episodes -= 1
    
    print(f"Total reward after {no_of_episodes} episodes: {total_reward}")
    print(f"Correct answers: {correct}, Wrong answers: {wrong}, Total: {correct + wrong}")
    return total_reward, correct, wrong 

if __name__ == '__main__':
    model_path = "./Trained_Models/PPO_1000000_1000000_steps.zip"
    eval(model_path, no_of_episodes=50)
