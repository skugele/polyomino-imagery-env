from PolyominoEnv import PolyominoEnvironment
from stable_baselines3 import PPO, DQN
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import CheckpointCallback

def test_model(model_path):
    env = PolyominoEnvironment()
    env = Monitor(env)
    model = PPO.load("./models/rl_model_224000_steps.zip")

    check_env(env, warn=True)

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

if __name__ == '__main__':
    model_path = "./models/rl_model_224000_steps.zip"
    test_model(model_path)
