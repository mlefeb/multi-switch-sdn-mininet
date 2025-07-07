#!/usr/bin/env python3

import yaml
import sys
import os

# Add the current directory to path to import from the main script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sdn_multi_topology_test import generate_universal_working_config

def test_config_generation():
    """Test if config generation creates all 10 switches"""
    
    print("🧪 TESTING CONFIG GENERATION FOR 10 SWITCHES")
    print("=" * 50)
    
    # Generate config for 10 switches, 2 hosts each
    config = generate_universal_working_config(10, 2)
    
    print(f"📊 Generated config has {len(config['dps'])} switches")
    print("\n🔍 Switch list:")
    for switch_name in sorted(config['dps'].keys()):
        dp_id = config['dps'][switch_name]['dp_id']
        print(f"  {switch_name}: dp_id={dp_id}")
    
    # Check if SW10 exists
    if 'sw10' in config['dps']:
        print("\n✅ SW10 is present in config!")
        sw10_config = config['dps']['sw10']
        print(f"   dp_id: {sw10_config['dp_id']}")
        print(f"   interfaces: {len(sw10_config['interfaces'])}")
        
        # Check specific interfaces
        if 1 in sw10_config['interfaces']:
            print(f"   h19 port: {sw10_config['interfaces'][1]['description']}")
        if 2 in sw10_config['interfaces']:
            print(f"   h20 port: {sw10_config['interfaces'][2]['description']}")
        if 3 in sw10_config['interfaces']:
            print(f"   trunk port 3: {sw10_config['interfaces'][3]['description']}")
    else:
        print("\n❌ SW10 is MISSING from config!")
        print("   This is the root cause of the isolation issue!")
    
    # Save the test config
    with open('test_10_switch_config.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"\n📝 Test config saved to: test_10_switch_config.yaml")
    print("   You can inspect this file to verify all switches are present")

if __name__ == '__main__':
    test_config_generation()