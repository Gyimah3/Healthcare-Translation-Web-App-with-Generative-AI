#!/bin/bash
# Update package lists
apt-get update && apt-get install -y \
    python3-dev \
    portaudio19-dev \
    gcc \
    libasound2-dev

# Install Python dependencies
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir -r requirements.txt