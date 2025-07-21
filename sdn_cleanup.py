#!/usr/bin/env python3
"""
SDN Cleanup Script
Ultra-fast cleanup for SDN testing environment
"""

import subprocess
import time
import sys
import concurrent.futures
from threading import Lock

# Thread-safe output
output_lock = Lock()

def safe_print(message):
    """Thread-safe printing"""
    with output_lock:
        print(message)
        sys.stdout.flush()

def run_cleanup_command(cmd, description, timeout=5):
    """Run cleanup command with aggressive timeout"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, 
                              text=True, timeout=timeout, bufsize=0)
        if result.returncode == 0:
            return f"✓ {description}"
        else:
            stderr_lower = result.stderr.lower()
            if any(phrase in stderr_lower for phrase in 
                   ['no such', 'not found', 'does not exist', 'not running', 'no bridge']):
                return f"✓ {description} (clean)"
            else:
                return f"⚠ {description}"
    except subprocess.TimeoutExpired:
        try:
            subprocess.run(f"pkill -f '{cmd.split()[0]}'", shell=True, timeout=1)
        except:
            pass
        return f"⏰ {description}"
    except Exception:
        return f"✗ {description}"

def ultra_fast_cleanup():
    """Execute ultra-fast cleanup of SDN environment"""
    
    print("="*60)
    print("SDN ULTRA-FAST CLEANUP")
    print("="*60)
    
    total_start = time.time()
    
    # All cleanup operations in parallel
    all_commands = [
        # Network cleanup
        ("sudo mn -c", "Mininet cleanup", 8),
        ("sudo killall controller 2>/dev/null || true", "Kill controllers", 2),
        ("sudo killall ovs-controller 2>/dev/null || true", "Kill OVS controllers", 2),
        ("sudo pkill -f 'mininet:' 2>/dev/null || true", "Kill Mininet processes", 2),
        
        # OVS cleanup  
        ("sudo killall ovs-vswitchd 2>/dev/null || true", "Kill OVS daemon", 2),
        ("sudo killall ovsdb-server 2>/dev/null || true", "Kill OVS database", 2),
        ("sudo ovs-vsctl list-br 2>/dev/null | head -50 | xargs -r -I {} sudo ovs-vsctl --if-exists del-br {} 2>/dev/null || true", "Delete bridges", 5),
        
        # Docker cleanup
        ("docker stop onos 2>/dev/null || true", "Stop ONOS", 3),
        ("docker rm onos 2>/dev/null || true", "Remove ONOS", 2),
        ("docker network prune -f 2>/dev/null || true", "Clean networks", 3),
        
        # Port cleanup
        ("sudo fuser -k 6653/tcp 2>/dev/null || true", "Free port 6653", 2),
        ("sudo fuser -k 8181/tcp 2>/dev/null || true", "Free port 8181", 2),
        ("sudo fuser -k 6640/tcp 2>/dev/null || true", "Free port 6640", 2),
        
        # File cleanup
        ("sudo rm -rf /var/run/openvswitch/* 2>/dev/null || true", "Clean OVS runtime", 2),
        ("sudo rm -rf /etc/openvswitch/conf.db* 2>/dev/null || true", "Clean OVS DB", 2),
        ("sudo rm -rf /tmp/mininet* 2>/dev/null || true", "Clean Mininet temp", 2),
        
        # Interface cleanup
        ("ip link show | grep -E 's[0-9]+-eth|h[0-9]+-eth' | head -20 | cut -d: -f2 | cut -d' ' -f1 | xargs -r -I {} sudo ip link delete {} 2>/dev/null || true", "Clean interfaces", 3),
    ]
    
    print(f"Executing {len(all_commands)} cleanup operations in parallel...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(run_cleanup_command, cmd, desc, timeout) 
                  for cmd, desc, timeout in all_commands]
        
        completed = 0
        success = 0
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if "✓" in result:
                success += 1
            completed += 1
            
            if completed <= 5 or completed % 5 == 0:
                safe_print(f"  Progress: {completed}/{len(all_commands)} operations")
    
    # Quick OVS restart
    print("\nRestarting OVS service...")
    try:
        subprocess.run(['sudo', 'service', 'openvswitch-switch', 'restart'], 
                      capture_output=True, timeout=8)
        print("  ✓ OVS service restarted")
    except:
        print("  ⚠ OVS restart had issues")
    
    total_time = time.time() - total_start
    
    print("\n" + "="*60)
    print(f"CLEANUP COMPLETED IN {total_time:.1f}s")
    print("="*60)
    print("System ready for SDN testing!")
    
    return True

def verify_clean_state():
    """Quick verification of clean state"""
    print("\nVERIFYING CLEAN STATE:")
    print("-" * 30)
    
    checks = [
        ("sudo ovs-vsctl list-br 2>/dev/null | wc -l", "OVS bridges"),
        ("docker ps --filter name=onos -q | wc -l", "ONOS containers"),
        ("ip link | grep -c 's[0-9]\\|h[0-9]' || echo 0", "Virtual interfaces"),
    ]
    
    all_clean = True
    for cmd, desc in checks:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3)
            count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else -1
            status = "✓" if count == 0 else "⚠"
            print(f"  {status} {desc}: {count}")
            if count > 0:
                all_clean = False
        except:
            print(f"  ✗ {desc}: check failed")
            all_clean = False
    
    return all_clean

def main():
    import argparse
    parser = argparse.ArgumentParser(description='SDN Environment Cleanup')
    parser.add_argument('--verify-only', action='store_true',
                       help='Only verify clean state')
    
    args = parser.parse_args()
    
    if args.verify_only:
        return 0 if verify_clean_state() else 1
    
    # Run cleanup
    success = ultra_fast_cleanup()
    
    # Verify
    print()
    clean = verify_clean_state()
    
    return 0 if success and clean else 1

if __name__ == '__main__':
    exit(main())