#!/bin/bash

# SDN Network Startup Script
# This script starts Faucet controller and creates the Mininet topology

set -e

echo "=== Starting SDN Network with Faucet Controller ==="

# Create log directory
mkdir -p faucet_logs

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Check if running as root (required for Mininet)
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    echo "Usage: sudo ./start_sdn.sh"
    exit 1
fi

# Stop any existing containers
echo "Stopping any existing Faucet containers..."
docker-compose down 2>/dev/null || true

# Start Faucet controller
echo "Starting Faucet controller..."
docker-compose up -d

# Wait for controller to be ready
echo "Waiting for Faucet controller to start..."
sleep 15

# Check if controller is running
if ! docker ps | grep -q faucet; then
    echo "Error: Faucet controller failed to start"
    docker-compose logs
    exit 1
fi

echo "Faucet controller started successfully!"
echo "Controller listening on port 6653"

# Make Mininet script executable
chmod +x mininet_topology.py

# Check if Mininet is installed
if ! command -v mn &> /dev/null; then
    echo "Error: Mininet is not installed"
    echo "Install with: sudo apt-get install mininet"
    exit 1
fi

# Clean up any existing Mininet state
echo "Cleaning up any existing Mininet state..."
mn -c > /dev/null 2>&1 || true

echo "Starting Mininet topology..."
echo "This will create 5 switches with 10 hosts across different IP ranges:"
echo "  - Switch 1: h1(10.0.1.10), h2(10.0.1.20)"
echo "  - Switch 2: h3(10.0.2.10), h4(10.0.2.20)" 
echo "  - Switch 3: h5(10.0.3.10), h6(10.0.3.20)"
echo "  - Switch 4: h7(10.0.4.10), h8(10.0.4.20)"
echo "  - Switch 5: h9(10.0.5.10), h10(10.0.5.20)"
echo ""
echo "Use 'pingall' in Mininet CLI to test cross-subnet connectivity"
echo ""

# Start Mininet topology
python3 mininet_topology.py

echo "=== SDN Network Demo Complete ==="