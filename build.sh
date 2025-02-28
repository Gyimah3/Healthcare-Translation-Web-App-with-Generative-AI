#!/usr/bin/env bash
set -o errexit

# Install system dependencies
apt-get update
apt-get install -y \
    build-essential \
    python3-dev \
    ffmpeg \
    libsndfile1

# Install Python dependencies
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir -r requirements.txt

# Create necessary directories
mkdir -p logs
chmod 777 logs
