#!/usr/bin/python3

from setuptools import setup, find_packages

DESCRIPTION = open("README.rst").read()

setup(
    name="spotmover",
    version="0.1",
    packages=find_packages(),
    author="Zsolt Cserna",
    author_email="cserna.zsolt@gmail.com",
    description="Migrate Google Play Music library to Spotify",
    long_description=DESCRIPTION,
    entry_points={
        'console_scripts': [
            'spotmover = spotmover.cli:main',
        ],
    },
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
)
