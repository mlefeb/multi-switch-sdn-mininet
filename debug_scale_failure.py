#!/usr/bin/env python3

"""
Debug why algorithm fails at 10+ switches
"""

import sys
import os
import yaml

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sdn_multi_topology_test import generate_universal_working_config

def debug_scale_failure():
    """Debug the specific failure at 10+ switches"""
    
    print("🔍 DEBUGGING SCALE FAILURE")
    print("=" * 40)
    
    # Test different switch counts around the failure point
    test_cases = [7, 8, 9, 10, 11, 12, 13]
    
    for num_switches in test_cases:
        print(f"\n📊 Testing {num_switches} switches (2 hosts each):")
        
        try:
            # Generate config
            config = generate_universal_working_config(num_switches, 2)
            
            # Basic validation
            actual_switches = len(config['dps'])
            print(f"   ✅ Config generated: {actual_switches} switches")
            
            # Check SW1 port requirements for star topology
            if 'sw1' in config['dps']:
                sw1_interfaces = config['dps']['sw1']['interfaces']
                max_port = max(sw1_interfaces.keys())
                
                # In star topology, SW1 needs:
                # - 2 host ports (1, 2)
                # - (num_switches - 1) trunk ports for other switches
                required_ports = 2 + (num_switches - 1)
                
                print(f"   SW1 max port: {max_port}, required: {required_ports}")
                
                if max_port >= required_ports:
                    print(f"   ✅ SW1 has sufficient ports")
                else:
                    print(f"   ❌ SW1 port exhaustion! Has {max_port}, needs {required_ports}")
            
            # Check last switch
            last_switch = f'sw{num_switches}'
            if last_switch in config['dps']:
                print(f"   ✅ {last_switch} present in config")
            else:
                print(f"   ❌ {last_switch} missing from config")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
    
    print(f"\n🔍 ANALYZING STAR TOPOLOGY PORT REQUIREMENTS:")
    print("=" * 50)
    
    for num_switches in [9, 10, 11, 12]:
        hosts_per_switch = 2
        
        # SW1 (central hub) requirements:
        host_ports = hosts_per_switch  # Usually 2
        trunk_ports = num_switches - 1  # Connections to other switches
        total_ports_needed = host_ports + trunk_ports
        
        print(f"{num_switches} switches:")
        print(f"   SW1 needs {host_ports} host ports + {trunk_ports} trunk ports = {total_ports_needed} total")
        
        # Check if this exceeds typical switch limits
        if total_ports_needed > 12:
            print(f"   ⚠️  Exceeds typical 12-port limit!")
        if total_ports_needed > 16:
            print(f"   ❌ Exceeds extended 16-port limit!")
        if total_ports_needed > 24:
            print(f"   ❌ Exceeds enterprise 24-port limit!")
    
    print(f"\n🔍 CHECKING TOPOLOGY CREATION LOGIC:")
    print("=" * 40)
    
    # Check the mesh topology creation for 10+ switches
    print("In mesh topology for 10+ switches:")
    print("- Uses hierarchical star pattern (should avoid SW1 port exhaustion)")
    print("- For ≤10 switches: single star (SW1 connects to all)")
    print("- For >10 switches: hierarchical star (distributed hubs)")
    
    print(f"\n🎯 HYPOTHESIS:")
    print("The failure at 10+ switches is likely due to:")
    print("1. SW1 port exhaustion in single star pattern")
    print("2. Physical topology creation failing")
    print("3. Controller overwhelming with too many simultaneous connections")
    print("4. Timeout insufficient for larger networks")

if __name__ == '__main__':
    debug_scale_failure()