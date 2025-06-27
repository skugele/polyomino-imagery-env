from BVAE import BVAE
from PolyominoEnv import PolyominoEnvironment
import tensorflow as tf
import numpy as np
from stable_baselines3 import PPO, DQN
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import CheckpointCallback
from sb3_contrib import RecurrentPPO
from stable_baselines3.common.evaluation import evaluate_policy

latent_dimensions = 16

def train_model(training_model, training_steps = 100000, buffer_size = 30000, load_model = None):
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
    # make random moves
    # for _ in range(30):
    #     obs, info = env.reset()
    #     action = env.action_space.sample()
    #     obs, reward, term, trun, info = env.step(action)
    #     print("Random Action:", action, "Reward:", reward)
    #     if term or trun:
    #         obs = env.reset()
    #         print("Resetting Environment")
    # return


    model = None
    model_name = training_model.__name__

    if load_model:
        print("Loading Saved Model ...", load_model)
        model = training_model.load(load_model, env=env, verbose=1, exploration_initial_eps=0.5, exploration_fraction=1)
    else:
        print("Setting up new model ...")
        if training_model.__name__ == "DQN":
            model = training_model("MultiInputPolicy", env, verbose=1, buffer_size=buffer_size, tensorboard_log="./tensorboard_logs/", exploration_fraction=1)
        elif training_model.__name__ == "PPO":
            model = training_model("MultiInputPolicy", env, verbose=1, tensorboard_log="./tensorboard_logs/")
        elif training_model.__name__ == "RecurrentPPO":
            model = training_model("MultiInputLstmPolicy", env, verbose=1, tensorboard_log="./tensorboard_logs/")


    model.learn(total_timesteps=training_steps, callback=checkpoint_callback)
    model.save(f"model-{training_model.__name__}-{training_steps}")


    obs, info = env.reset()
    while True:
        action, _ = model.predict(obs)
        obs, reward, term, trun, info = env.step(action)
        print(action, reward)
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

    latest_model_path = get_latest_model()
    print(latest_model_path)

    train_model(DQN, training_steps=20000000, load_model=latest_model_path)
