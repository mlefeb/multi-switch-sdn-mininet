#!/bin/bash

echo "=== Testing Single Subnet SDN Network ==="
echo ""
echo "This test uses all hosts in 10.0.0.0/8 subnet for L2 switching"
echo "which should make pingall work across all 5 switches."
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    echo "Usage: sudo ./test_single_subnet.sh"
    exit 1
fi

# Clean up any existing Mininet state
echo "Cleaning up existing Mininet state..."
mn -c > /dev/null 2>&1 || true

echo "Starting single subnet topology test..."
echo ""
python3 single_subnet_topology.py