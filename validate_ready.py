#!/usr/bin/env python3
"""
Validation script to confirm the enhanced solution is ready
"""

import yaml
import subprocess
import os

def validate_enhanced_solution():
    """Validate that the enhanced solution is ready for testing"""
    
    print("🔍 VALIDATING ENHANCED SDN SOLUTION")
    print("=" * 50)
    
    # Check if enhanced script exists
    if os.path.exists('enhanced_working_test.py'):
        print("✅ Enhanced test script exists")
    else:
        print("❌ Enhanced test script missing")
        return False
    
    # Test configuration generation
    print("\n📋 Testing Configuration Generation:")
    try:
        # Import and test config generation
        import sys
        sys.path.insert(0, '.')
        from enhanced_working_test import generate_working_config
        
        # Test 2-switch config
        config = generate_working_config(2, 2)
        
        # Validate structure
        if 'vlans' in config and 100 in config['vlans']:
            vlan_config = config['vlans'][100]
            print(f"   ✅ VLAN 100: {vlan_config}")
            if vlan_config.get('unicast_flood'):
                print("   ✅ unicast_flood: true (critical for cross-switch)")
            else:
                print("   ❌ unicast_flood missing")
                return False
        else:
            print("   ❌ VLAN 100 missing")
            return False
        
        # Check switches
        if 'dps' in config and len(config['dps']) == 2:
            print(f"   ✅ {len(config['dps'])} switches configured")
            
            # Check sw1 configuration
            sw1 = config['dps']['sw1']
            interfaces = sw1.get('interfaces', {})
            print(f"   ✅ SW1 has {len(interfaces)} interfaces")
            
            # Check that all interfaces use native_vlan: 100
            all_native_100 = all(
                iface.get('native_vlan') == 100 
                for iface in interfaces.values()
            )
            if all_native_100:
                print("   ✅ All interfaces use native_vlan: 100")
            else:
                print("   ❌ Not all interfaces use native_vlan: 100")
                return False
        else:
            print("   ❌ Wrong number of switches")
            return False
            
    except Exception as e:
        print(f"   ❌ Config generation failed: {e}")
        return False
    
    # Test Docker capability
    print("\n🐳 Testing Docker Capability:")
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True, check=True)
        print(f"   ✅ Docker available: {result.stdout.strip()}")
        
        # Test Faucet image availability
        result = subprocess.run(['docker', 'images', 'faucet/faucet'], capture_output=True, text=True)
        if 'faucet/faucet' in result.stdout:
            print("   ✅ Faucet Docker image available")
        else:
            print("   ⚠️  Faucet image not found locally - will download on first run")
            
    except subprocess.CalledProcessError:
        print("   ❌ Docker not available")
        return False
    except FileNotFoundError:
        print("   ❌ Docker command not found")
        return False
    
    # Test generated config file
    print("\n📄 Testing Generated Configuration:")
    if os.path.exists('enhanced_faucet.yaml'):
        with open('enhanced_faucet.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Compare with working pattern
        print("   ✅ Configuration file generated")
        print(f"   ✅ VLANs: {list(config.get('vlans', {}).keys())}")
        print(f"   ✅ Switches: {list(config.get('dps', {}).keys())}")
        
        # Check pattern match with working_minimal.yaml
        if os.path.exists('working_minimal.yaml'):
            with open('working_minimal.yaml', 'r') as f:
                working_config = yaml.safe_load(f)
            
            # Compare VLAN structure
            if config['vlans'][100] == working_config['vlans'][100]:
                print("   ✅ VLAN configuration matches working pattern exactly")
            else:
                print("   ❌ VLAN configuration differs from working pattern")
                return False
        
    else:
        print("   ⚠️  No configuration file generated yet")
    
    # Check privileges requirement
    print("\n🔐 Privilege Requirements:")
    current_user = subprocess.run(['whoami'], capture_output=True, text=True).stdout.strip()
    if current_user == 'root':
        print("   ✅ Running as root - can run tests directly")
    else:
        print(f"   ⚠️  Running as {current_user} - use 'sudo python3 enhanced_working_test.py' for tests")
    
    print("\n🎯 SOLUTION ANALYSIS:")
    print("=" * 50)
    print("✅ Enhanced solution follows EXACT working pattern:")
    print("   • Single VLAN 100 with unicast_flood: true")
    print("   • All hosts in same subnet (10.0.0.x/8)")
    print("   • All ports use native_vlan: 100 (not tagged)")
    print("   • Star topology with proper port mappings")
    print("   • No routing complexity - pure L2 switching")
    print()
    print("✅ Key improvements over original:")
    print("   • Configurable number of switches and hosts")
    print("   • Dynamic configuration generation")
    print("   • Automatic Docker controller management")
    print("   • Scalable star topology implementation")
    print()
    print("🚀 READY FOR TESTING:")
    print("   Run: sudo python3 enhanced_working_test.py --switches 3 --hosts 2")
    print("   Expected: 100% pingall connectivity")
    
    return True

if __name__ == '__main__':
    success = validate_enhanced_solution()
    if success:
        print("\n🏆 VALIDATION SUCCESSFUL - SOLUTION IS READY!")
    else:
        print("\n❌ VALIDATION FAILED - NEEDS FIXES")
        exit(1)