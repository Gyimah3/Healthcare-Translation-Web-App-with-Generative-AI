#!/bin/bash
apt-get update
apt-get install -y python3-dev portaudio19-dev python3-pyaudio
pip install --upgrade pip
pip install wheel setuptools
pip install -r requirements.txt