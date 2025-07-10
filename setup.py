from setuptools import find_packages
from setuptools import setup


# Read dependencies from requirements.txt
def load_requirements(path):
    with open(path) as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]


setup(
    name="polyomino-env",
    version="0.0.1",
    description="A polyomino environment intended for mental imagery experiments on humans and "
                "software agents.",
    author="Sean Kugele",
    author_email="kugeles@rhodes.edu",
    packages=find_packages(),
    install_requires=load_requirements("requirements.txt"),
    python_requires=">=3.11",
)
