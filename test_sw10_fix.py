#!/usr/bin/env python3

"""
Test the SW10 fix - verify config includes all 10 switches
"""

import yaml

def test_sw10_fix():
    """Test that SW10 is now properly configured"""
    
    print("🧪 TESTING SW10 FIX")
    print("=" * 40)
    
    # Load the current config
    with open('universal_mesh_faucet.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Check switches
    switches = config.get('dps', {})
    print(f"📊 Total switches in config: {len(switches)}")
    
    # List all switches
    for sw_name in sorted(switches.keys()):
        dp_id = switches[sw_name]['dp_id']
        interface_count = len(switches[sw_name]['interfaces'])
        print(f"  {sw_name}: dp_id={dp_id}, interfaces={interface_count}")
    
    # Check SW10 specifically
    if 'sw10' in switches:
        print("\n✅ SW10 FOUND IN CONFIG!")
        sw10 = switches['sw10']
        print(f"   dp_id: {sw10['dp_id']}")
        print(f"   interfaces: {len(sw10['interfaces'])}")
        
        # Check key interfaces
        if 1 in sw10['interfaces']:
            print(f"   Port 1: {sw10['interfaces'][1]['description']}")
        if 2 in sw10['interfaces']:
            print(f"   Port 2: {sw10['interfaces'][2]['description']}")
        if 3 in sw10['interfaces']:
            print(f"   Port 3: {sw10['interfaces'][3]['description']}")
        
        print("\n🎯 EXPECTED BEHAVIOR:")
        print("   - SW10 should now connect to Faucet controller")
        print("   - Flows should be installed on SW10")
        print("   - h19 and h20 should achieve connectivity")
        print("   - Overall success rate should improve from 80.5%")
        
    else:
        print("\n❌ SW10 STILL MISSING!")
        print("   The fix did not work properly")
    
    # Check VLAN configuration
    vlans = config.get('vlans', {})
    if 100 in vlans:
        print(f"\n✅ VLAN 100 configured:")
        print(f"   unicast_flood: {vlans[100].get('unicast_flood', False)}")
    
    print("\n🚀 READY FOR TESTING!")
    print("Run: python3 sdn_multi_topology_test.py --topology mesh --switches 10 --hosts 2 --no-cli")

if __name__ == '__main__':
    test_sw10_fix()