#!/usr/bin/env python3

"""
Debug specific sw10 connectivity issue
"""

def debug_sw10_connectivity():
    """
    Debug why sw10 (h19, h20) is isolated
    """
    
    print("🔍 SW10 CONNECTIVITY DEBUG")
    print("=" * 40)
    
    print("\n📊 OBSERVED SYMPTOMS:")
    print("- ❌ SW10 has no flows installed")
    print("- ❌ h19 and h20 completely isolated (all X's)")
    print("- ✅ h1-h18 have 80.5% connectivity")
    print("- ✅ Cross-switch communication works for h1-h18")
    
    print("\n🔍 POTENTIAL ROOT CAUSES:")
    
    print("\n1. 🔌 PHYSICAL CONNECTIVITY:")
    print("   - SW10 may not be physically connected to network")
    print("   - Star pattern: SW1 should connect to SW10 on specific ports")
    print("   - Expected: SW1 port 11 <-> SW10 port 3")
    
    print("\n2. 📋 CONTROLLER CONNECTION:")
    print("   - SW10 may not be connecting to Faucet controller")
    print("   - No flows installed suggests controller communication failure")
    print("   - Need to verify OpenFlow connection")
    
    print("\n3. 🏷️ DPID MISMATCH:")
    print("   - SW10 DPID may not match Faucet configuration")
    print("   - Mininet: dpid='10', Faucet: dp_id: 10")
    print("   - Faucet may not recognize SW10")
    
    print("\n4. ⏱️ TIMING ISSUES:")
    print("   - Large topology may need longer flow installation time")
    print("   - 20 seconds may not be enough for 10 switches")
    
    print("\n🛠️ DEBUG STEPS TO TRY:")
    
    print("\n1. 🔍 CHECK PHYSICAL TOPOLOGY:")
    print("   - Verify SW1-SW10 link exists")
    print("   - Check port assignments in Mininet creation")
    print("   - Use 'net' command in CLI to show topology")
    
    print("\n2. 🔗 CHECK CONTROLLER CONNECTION:")
    print("   - ovs-vsctl show # Check controller assignment")
    print("   - ovs-vsctl get-controller sw10 # Verify controller IP")
    print("   - docker logs universal-faucet | grep sw10 # Check Faucet logs")
    
    print("\n3. 📊 CHECK FLOWS:")
    print("   - ovs-ofctl dump-flows sw10 # Check if any flows exist")
    print("   - ovs-ofctl dump-ports sw10 # Check port status")
    
    print("\n4. ⏱️ INCREASE TIMING:")
    print("   - Increase flow installation wait time to 60 seconds")
    print("   - Check if sw10 flows appear with more time")
    
    print("\n🎯 MOST LIKELY FIX:")
    print("The issue is probably:")
    print("1. SW10 physical connection missing in large-scale star")
    print("2. OR controller connection timing for 10th switch")
    print("3. OR port assignment bug in star topology creation")

if __name__ == '__main__':
    debug_sw10_connectivity()