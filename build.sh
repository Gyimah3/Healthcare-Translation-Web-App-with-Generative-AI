# #!/usr/bin/env bash
# # exit on error
# set -o errexit

# # Update packages and install dependencies
# apt-get update
# apt-get install -y python3-dev

# # Upgrade pip and install requirements
# pip install --upgrade pip
# pip install -r requirements.txt

# # portaudio19-dev

#!/usr/bin/env bash
# # exit on error
# set -o errexit

# # Update packages
# apt-get update -y

# # Install PortAudio development libraries with explicit paths
# apt-get install -y portaudio19-dev python3-all-dev pkg-config

# # Update LD_LIBRARY_PATH to help find the libraries
# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib:/usr/lib

# # Make sure pkg-config can find PortAudio
# export PKG_CONFIG_PATH=$PKG_CONFIG_PATH:/usr/local/lib/pkgconfig:/usr/lib/pkgconfig
 
# # Install Python dependencies
# pip install --upgrade pip

# # Install PyAudio first with specific compilation flags
# pip install --global-option="build_ext" --global-option="-I/usr/include" --global-option="-L/usr/lib" pyaudio

# # Install the rest of the requirements
# pip install -r requirements.txt

#!/usr/bin/env bash
# exit on error
set -o errexit

# Update package list
apt-get update -y

# Install essential build tools and dependencies
apt-get install -y build-essential libasound2-dev python3-dev python3-setuptools python3-numpy python3-cffi

# Download and build PortAudio from source
cd /tmp
wget http://files.portaudio.com/archives/pa_stable_v190700_20210406.tgz
tar -zxvf pa_stable_v190700_20210406.tgz
cd portaudio
./configure --with-alsa
make
make install
ldconfig

# Update pip and install other requirements that don't include PyAudio
pip install --upgrade pip

# Now try to install PyAudio
pip install pyaudio

# Install remaining requirements
pip install -r requirements.txt