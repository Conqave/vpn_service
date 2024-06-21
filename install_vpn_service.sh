#!/bin/bash

set -e

# Update and install necessary packages
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip git iproute2

# Clone the repository
git clone https://github.com/Conqave/vpn_service.git
cd vpn_service

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install required Python packages
pip install --upgrade pip
pip install pycryptodome pyroute2

echo "Creating TUN device..."
# Create and configure TUN device
sudo ip tuntap add dev tun0 mode tun
sudo ip addr add 10.8.0.1/24 dev tun0
sudo ip link set dev tun0 up

echo "Starting SOCKS5 server..."
# Start the SOCKS5 server
python socks5_server.py &

echo "Configuration complete. Please run vpn_tun.py with sudo:"
echo "source venv/bin/activate && sudo venv/bin/python vpn_tun.py"
