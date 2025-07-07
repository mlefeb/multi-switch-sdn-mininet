#!/usr/bin/env python3

def analyze_mesh_topology(num_switches, hosts_per_switch):
    """Analyze mesh topology port assignments"""
    
    print(f"=== MESH TOPOLOGY ANALYSIS ===")
    print(f"Switches: {num_switches}, Hosts per switch: {hosts_per_switch}")
    
    # Calculate mesh connections
    total_connections = (num_switches * (num_switches - 1)) // 2
    print(f"Total mesh connections needed: {total_connections}")
    
    # Analyze port usage per switch
    port_map = {}
    for i in range(num_switches):
        port_map[i] = hosts_per_switch + 1  # Start trunk ports after host ports
    
    connections = []
    print(f"\nConnection plan:")
    for i in range(num_switches):
        for j in range(i + 1, num_switches):
            connection = (i+1, port_map[i], j+1, port_map[j])
            connections.append(connection)
            print(f"  sw{i+1} port {port_map[i]} <--> sw{j+1} port {port_map[j]}")
            port_map[i] += 1
            port_map[j] += 1
    
    print(f"\nFinal port usage:")
    for i in range(num_switches):
        final_port = port_map[i] - 1
        total_ports_needed = hosts_per_switch + (final_port - hosts_per_switch)
        print(f"  sw{i+1}: host ports 1-{hosts_per_switch}, trunk ports {hosts_per_switch+1}-{final_port}")
        print(f"         total ports needed: {final_port}")
    
    # Check if this matches our universal config
    max_connections_per_switch = num_switches - 1
    print(f"\nUniversal config provides:")
    for i in range(num_switches):
        provided_trunk_ports = max_connections_per_switch
        print(f"  sw{i+1}: trunk ports {hosts_per_switch+1}-{hosts_per_switch+provided_trunk_ports}")
    
    # Check for port conflicts
    print(f"\nPotential issues:")
    max_port_used = max(port_map[i] - 1 for i in range(num_switches))
    max_port_provided = hosts_per_switch + max_connections_per_switch
    
    if max_port_used > max_port_provided:
        print(f"  ❌ ISSUE: Need port {max_port_used}, but only provide up to {max_port_provided}")
        print(f"     Solution: Increase trunk port range or reduce connections")
    else:
        print(f"  ✅ OK: Max port used {max_port_used} <= Max provided {max_port_provided}")
    
    return connections

def compare_topologies():
    """Compare port usage across different topologies"""
    
    print("\n" + "="*60)
    print("TOPOLOGY COMPARISON")
    print("="*60)
    
    configs = [
        ("star", 3, 2),
        ("mesh", 3, 2), 
        ("tree", 3, 2),
        ("linear", 3, 2)
    ]
    
    for topology, switches, hosts in configs:
        print(f"\n{topology.upper()} topology ({switches} switches, {hosts} hosts/switch):")
        
        if topology == "star":
            # Star: central switch connects to all others
            print(f"  sw1: connects to sw2, sw3 (2 connections)")
            print(f"  sw2: connects to sw1 (1 connection)")  
            print(f"  sw3: connects to sw1 (1 connection)")
            print(f"  Max ports per switch: {hosts + 2}")
            
        elif topology == "mesh":
            # Mesh: full connectivity
            connections = analyze_mesh_topology(switches, hosts)
            
        elif topology == "tree":
            # Tree: hierarchical
            print(f"  sw1: connects to sw2, sw3 (2 connections)")
            print(f"  sw2: connects to sw1 (1 connection)")
            print(f"  sw3: connects to sw1 (1 connection)")
            print(f"  Max ports per switch: {hosts + 1}")
            
        elif topology == "linear":
            # Linear: chain
            print(f"  sw1: connects to sw2 (1 connection)")
            print(f"  sw2: connects to sw1, sw3 (2 connections)")
            print(f"  sw3: connects to sw2 (1 connection)")
            print(f"  Max ports per switch: {hosts + 2}")

if __name__ == '__main__':
    analyze_mesh_topology(3, 2)
    compare_topologies()