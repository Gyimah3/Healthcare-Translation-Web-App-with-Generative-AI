#!/usr/bin/env bash
# exit on error
set -o errexit

# Update packages and install dependencies
apt-get update
apt-get install -y python3-dev

# Upgrade pip and install requirements
pip install --upgrade pip
pip install -r requirements.txt

# portaudio19-dev