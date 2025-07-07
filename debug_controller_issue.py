#!/usr/bin/env python3

"""
Debug why SW15-SW20 consistently fail across topologies
"""

def analyze_controller_issue():
    """Analyze why SW15-SW20 fail across different topologies"""
    
    print("🔍 DEBUGGING SW15-SW20 CONTROLLER ISSUE")
    print("=" * 50)
    
    print("\n❌ CONSISTENT FAILURE PATTERN:")
    print("- SW1-SW14: ✅ Flows installed")
    print("- SW15-SW20: ❌ No flows installed")
    print("- Occurs in: mesh, tree topologies")
    print("- Pattern: Always switches 15-20, regardless of topology")
    
    print("\n🔍 POSSIBLE ROOT CAUSES:")
    
    print("\n1. 🐳 DOCKER CONTROLLER LIMITS:")
    print("   - Faucet controller may have connection limits")
    print("   - Docker container resource constraints")
    print("   - Controller overwhelmed by 20 simultaneous connections")
    
    print("\n2. 📊 FAUCET CONFIGURATION ISSUES:")
    print("   - Config file may have issues for SW15-SW20")
    print("   - YAML parsing problems at end of file")
    print("   - DP ID conflicts or invalid configurations")
    
    print("\n3. ⏱️ TIMING ISSUES:")
    print("   - SW15-SW20 connect after controller capacity reached")
    print("   - Flow installation timeout before reaching these switches")
    print("   - Race condition in controller handshake")
    
    print("\n4. 🔌 OPENFLOW CONNECTION LIMITS:")
    print("   - Default OpenFlow connection limits")
    print("   - Port exhaustion on controller side")
    print("   - Network namespace issues")
    
    print("\n🛠️ DEBUGGING STEPS:")
    
    print("\n1. 📋 CHECK FAUCET CONFIG:")
    print("   grep -A 10 'sw15\\|sw16\\|sw17\\|sw18\\|sw19\\|sw20' universal_*_faucet.yaml")
    print("   # Verify SW15-SW20 are properly defined")
    
    print("\n2. 🐳 CHECK DOCKER LOGS:")
    print("   docker logs universal-faucet | grep -i 'sw1[5-9]\\|sw20'")
    print("   # Look for connection/error messages")
    
    print("\n3. 🔗 TEST CONNECTION LIMITS:")
    print("   # Try with fewer switches to find the limit")
    print("   sudo python3 sdn_multi_topology_test.py --topology linear --switches 15 --hosts 2")
    print("   sudo python3 sdn_multi_topology_test.py --topology linear --switches 16 --hosts 2")
    
    print("\n4. ⚙️ TEST DIFFERENT CONTROLLER:")
    print("   # Try without Docker (if possible)")
    print("   # Or increase Docker resources")
    
    print("\n🎯 MOST LIKELY CAUSES:")
    print("1. **Faucet controller connection limit** (most likely)")
    print("2. **Docker container resource constraint**")
    print("3. **OpenFlow protocol limits**")
    
    print("\n💡 QUICK TESTS TO ISOLATE:")
    
    print("\n🧪 Test A: Find the exact limit")
    print("for i in {12..18}; do")
    print("  echo \"Testing $i switches:\"")
    print("  sudo python3 sdn_multi_topology_test.py --topology linear --switches $i --hosts 2 --no-cli | grep 'failed_switches'")
    print("done")
    
    print("\n🧪 Test B: Check if it's always switches 15-20 or last 6")
    print("sudo python3 sdn_multi_topology_test.py --topology linear --switches 10 --hosts 2")
    print("# Should work if issue is specific to SW15-SW20")
    
    print("\n🧪 Test C: Check Faucet config")
    print("python3 -c \"import yaml; print(len(yaml.safe_load(open('universal_tree_s20_h2_faucet.yaml'))['dps']))\"")
    print("# Should print 20 if all switches in config")

if __name__ == '__main__':
    analyze_controller_issue()