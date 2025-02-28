#!/bin/bash
# Update packages
apt-get update

# Install PortAudio development libraries and other necessary packages
apt-get install -y portaudio19-dev python3-all-dev

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt