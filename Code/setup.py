from setuptools import setup, find_packages

setup(
    name="AdaptiveTrafficSignal",
    version="1.0.0",
    description="A Python simulation of an adaptive traffic signal system using Pygame.",
    author="Your Name",
    license="MIT",
    packages=find_packages(exclude=["tests*", "darkflow*"]),
    install_requires=[
        "pygame>=2.6.1",
        "matplotlib>=3.10.0"
    ],
    entry_points={
        "console_scripts": [
            "traffic-sim = simulation:main"
        ]
    },
)
