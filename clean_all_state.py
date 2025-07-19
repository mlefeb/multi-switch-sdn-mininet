#!/usr/bin/env python3
"""
Clean all SDN state, caches, and restart fresh
"""

import subprocess
import time
import os

def run_command(cmd, description):
    """Run command and report status"""
    print(f">>> {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"    ✓ Success")
            if result.stdout.strip():
                print(f"    {result.stdout.strip()}")
        else:
            print(f"    ⚠ Failed: {result.stderr.strip()}")
    except Exception as e:
        print(f"    ✗ Error: {e}")

print("="*60)
print("CLEANING ALL SDN STATE AND CACHES")
print("="*60)

# 1. Clean Mininet state
print("\n1. CLEANING MININET STATE")
run_command("sudo mn -c", "Clean all Mininet state")

# 2. Kill any lingering OVS processes
print("\n2. CLEANING OVS PROCESSES")
run_command("sudo killall ovs-controller 2>/dev/null || true", "Kill OVS controllers")
run_command("sudo killall ovsdb-server 2>/dev/null || true", "Kill OVSDB server")
run_command("sudo killall ovs-vswitchd 2>/dev/null || true", "Kill OVS daemon")

# 3. Clean OVS database
print("\n3. CLEANING OVS DATABASE")
run_command("sudo ovs-vsctl --if-exists del-br s1", "Remove test bridges")
run_command("sudo ovs-vsctl --if-exists del-br s2", "Remove test bridges")
run_command("sudo ovs-vsctl --if-exists del-br s3", "Remove test bridges")
run_command("sudo ovs-vsctl list-br | xargs -r -n 1 sudo ovs-vsctl del-br", "Remove all bridges")
run_command("sudo rm -rf /var/run/openvswitch/*", "Clean OVS runtime files")
run_command("sudo rm -rf /etc/openvswitch/*.db", "Clean OVS database files")

# 4. Restart OVS service
print("\n4. RESTARTING OVS SERVICE")
run_command("sudo service openvswitch-switch restart", "Restart OVS service")
time.sleep(3)

# 5. Clean ONOS state
print("\n5. CLEANING ONOS STATE")
run_command("docker exec onos rm -rf /root/onos/data/db/*", "Clean ONOS database")
run_command("docker exec onos rm -rf /root/onos/apache-karaf-*/data/cache/*", "Clean ONOS cache")

# 6. Restart ONOS container
print("\n6. RESTARTING ONOS")
run_command("docker restart onos", "Restart ONOS container")
print("    Waiting 30s for ONOS to fully start...")
time.sleep(30)

# 7. Re-activate ONOS apps
print("\n7. RE-ACTIVATING ONOS APPS")
time.sleep(10)  # Extra wait for ONOS to be ready
run_command("docker exec onos /root/onos/bin/onos-app localhost activate org.onosproject.openflow", "Activate OpenFlow")
time.sleep(2)
run_command("docker exec onos /root/onos/bin/onos-app localhost activate org.onosproject.fwd", "Activate Forwarding")
time.sleep(2)

# 8. Verify ONOS status
print("\n8. VERIFYING ONOS STATUS")
run_command("docker exec onos /root/onos/bin/onos localhost apps -a -s | grep -E '(openflow|fwd)'", "Check active apps")

# 9. Clean any stale network interfaces
print("\n9. CLEANING NETWORK INTERFACES")
run_command("sudo ip link | grep -E 's[0-9]+-eth|h[0-9]+-eth' | cut -d: -f2 | xargs -r -n1 sudo ip link delete", "Delete stale interfaces")

# 10. Clear iptables rules that might interfere
print("\n10. CLEANING IPTABLES")
run_command("sudo iptables -F", "Flush iptables")
run_command("sudo iptables -t nat -F", "Flush NAT table")

print("\n" + "="*60)
print("CLEANUP COMPLETE - SYSTEM IS FRESH")
print("="*60)
print("\nYou can now run your tests with a clean state.")
print("Wait 10 more seconds before running tests to ensure ONOS is fully ready.")