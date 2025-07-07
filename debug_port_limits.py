#!/usr/bin/env python3

"""
Debug port limits and physical topology creation
"""

def debug_port_assignments():
    """Debug the exact port assignments for different switch counts"""
    
    print("🔍 DEBUGGING PORT ASSIGNMENTS")
    print("=" * 40)
    
    hosts_per_switch = 2
    
    for num_switches in [8, 9, 10, 11, 12]:
        print(f"\n📊 {num_switches} switches analysis:")
        
        # SW1 (central hub) port assignments
        print(f"   SW1 ports:")
        print(f"     1-2: hosts (h1, h2)")
        
        trunk_ports = []
        for i in range(1, num_switches):  # SW2, SW3, ..., SW{num_switches}
            central_port = hosts_per_switch + i
            trunk_ports.append(central_port)
            print(f"     {central_port}: SW{i+1}")
        
        max_port = max(trunk_ports)
        print(f"   SW1 max port used: {max_port}")
        
        # Check other switches
        print(f"   SW{num_switches} ports:")
        print(f"     1-2: hosts (h{(num_switches-1)*2+1}, h{num_switches*2})")
        print(f"     3: connection to SW1 port {max_port}")
        
        # Port limit analysis
        if max_port > 10:
            print(f"   ⚠️  Uses port {max_port} (>10)")
        if max_port > 12:
            print(f"   ❌ Uses port {max_port} (>12) - may hit OVS limits")
        if max_port > 16:
            print(f"   ❌ Uses port {max_port} (>16) - definitely problematic")
    
    print(f"\n🔍 POTENTIAL ISSUES:")
    print("=" * 20)
    print("1. OpenFlow port numbering: Some implementations limit ports")
    print("2. OVS default limits: May have default port count restrictions")
    print("3. Mininet constraints: Virtual switch port limits")
    print("4. Interface naming: eth0-eth{N} may have limits")
    
    print(f"\n🎯 ROOT CAUSE HYPOTHESIS:")
    print("The failure at 10+ switches is likely because:")
    print("- SW1 uses port 11+ for connections")
    print("- OpenFlow/OVS may have default limits around 10-12 ports")
    print("- Virtual switch constraints in Mininet")
    print("- Controller may timeout with too many ports per switch")
    
    print(f"\n🛠️ POTENTIAL FIXES:")
    print("1. Use hierarchical star for 10+ switches (already implemented)")
    print("2. Reduce the threshold: use hierarchical for 9+ switches")
    print("3. Verify OVS port limits and increase if needed")
    print("4. Add port validation in topology creation")

if __name__ == '__main__':
    debug_port_assignments()