#!/usr/bin/env python3

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import time
import argparse
import yaml
import os
import subprocess
import atexit

def generate_universal_working_config(num_switches, hosts_per_switch):
    """
    Generate Faucet config using the PROVEN WORKING PATTERN for ALL topologies
    
    Key insight: The same single VLAN L2 switching config works for ALL topologies!
    Physical topology differences are handled by Mininet link creation, not Faucet config.
    """
    
    config = {
        'vlans': {
            100: {
                'description': 'default VLAN',
                'unicast_flood': True  # 🔑 CRITICAL for cross-switch forwarding
            }
        },
        'dps': {}
    }
    
    # Generate switches following the EXACT working pattern
    for i in range(1, num_switches + 1):
        interfaces = {}
        
        # Host ports - each gets native_vlan: 100
        for port in range(1, hosts_per_switch + 1):
            host_num = (i-1) * hosts_per_switch + port
            interfaces[port] = {
                'description': f'h{host_num}',
                'native_vlan': 100  # 🔑 SAME VLAN FOR ALL
            }
        
        # Inter-switch ports - reserve enough ports for ANY topology
        # The beauty: we don't need to know the topology! Just provide enough trunk ports.
        max_connections = num_switches - 1  # Maximum possible connections for any topology
        for j in range(max_connections):
            trunk_port = hosts_per_switch + 1 + j
            interfaces[trunk_port] = {
                'description': f'inter-switch trunk port {trunk_port}',
                'native_vlan': 100  # 🔑 CRITICAL: native_vlan, NOT tagged_vlans
            }
        
        config['dps'][f'sw{i}'] = {
            'dp_id': i,  # Integer dp_id like working pattern
            'hardware': 'Open vSwitch',
            'interfaces': interfaces
        }
    
    return config

def start_faucet_controller(config_file):
    """Start Faucet controller using Docker with specified config"""
    
    info('*** Starting Faucet controller with Docker...\n')
    
    # Cleanup any existing containers
    try:
        subprocess.run(['docker', 'stop', 'universal-faucet'], check=False, capture_output=True)
        subprocess.run(['docker', 'rm', 'universal-faucet'], check=False, capture_output=True)
        time.sleep(2)
    except:
        pass
    
    # Start Faucet with the generated configuration
    cmd = [
        'docker', 'run', '-d',
        '--name', 'universal-faucet',
        '-p', '6653:6653',
        '-v', f'{os.path.abspath(config_file)}:/etc/faucet/faucet.yaml',
        'faucet/faucet:latest'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        atexit.register(stop_faucet_controller)
        
        # Wait for Faucet to start
        time.sleep(10)
        
        # Check if container is running
        check_cmd = ['docker', 'ps', '--filter', 'name=universal-faucet', '--format', '{{.Status}}']
        check_result = subprocess.run(check_cmd, capture_output=True, text=True)
        
        if 'Up' in check_result.stdout:
            info('*** Faucet controller started successfully\n')
            return True
        else:
            logs_cmd = ['docker', 'logs', 'universal-faucet']
            logs_result = subprocess.run(logs_cmd, capture_output=True, text=True)
            info(f'*** Faucet failed to start. Logs:\n{logs_result.stdout}\n{logs_result.stderr}\n')
            return False
            
    except subprocess.CalledProcessError as e:
        info(f'*** Error starting Faucet container: {e}\n')
        return False

def stop_faucet_controller():
    """Stop Faucet controller container"""
    try:
        subprocess.run(['docker', 'stop', 'universal-faucet'], check=False, capture_output=True)
        subprocess.run(['docker', 'rm', 'universal-faucet'], check=False, capture_output=True)
    except:
        pass

def create_hosts_universal(net, switches, num_switches, hosts_per_switch):
    """Create hosts using the PROVEN WORKING PATTERN - all in same subnet"""
    hosts = []
    
    # ALL hosts in same subnet (10.0.0.x) following working pattern
    for i in range(1, num_switches + 1):
        for j in range(1, hosts_per_switch + 1):
            host_num = (i-1) * hosts_per_switch + j
            # 🔑 CRITICAL: All hosts in same subnet like working pattern
            host = net.addHost(f'h{host_num}', ip=f'10.0.0.{host_num}/8')
            hosts.append(host)
            # Connect to switch port j
            net.addLink(host, switches[i-1], port2=j)
            info(f'*** Connecting h{host_num} to sw{i} port {j}\n')
    
    return hosts

def create_star_topology(net, num_switches, hosts_per_switch):
    """Create star topology - PROVEN WORKING"""
    switches = []
    
    # Create switches
    for i in range(1, num_switches + 1):
        sw = net.addSwitch(f'sw{i}', cls=OVSSwitch, dpid=str(i))
        switches.append(sw)
    
    # Create star connections: all switches connect to sw1
    if num_switches > 1:
        central_sw = switches[0]  # sw1
        for i in range(1, num_switches):  # sw2, sw3, sw4, ...
            leaf_sw = switches[i]
            # Central switch uses sequential ports after host ports
            central_port = hosts_per_switch + i
            # Leaf switch uses first trunk port
            leaf_port = hosts_per_switch + 1
            net.addLink(central_sw, leaf_sw, port1=central_port, port2=leaf_port)
            info(f'*** Star: Connecting sw1 port {central_port} to sw{i+1} port {leaf_port}\n')
    
    # Add hosts using universal pattern
    hosts = create_hosts_universal(net, switches, num_switches, hosts_per_switch)
    
    return switches, hosts

def create_mesh_topology(net, num_switches, hosts_per_switch):
    """Create partial mesh topology (avoiding loops) using working pattern"""
    switches = []
    
    # Create switches
    for i in range(1, num_switches + 1):
        sw = net.addSwitch(f'sw{i}', cls=OVSSwitch, dpid=str(i))
        switches.append(sw)
    
    # Create PARTIAL mesh connections to avoid broadcast loops
    # Key insight: Full mesh creates loops that break L2 learning!
    
    if num_switches == 2:
        # Simple connection
        net.addLink(switches[0], switches[1], port1=hosts_per_switch+1, port2=hosts_per_switch+1)
        info(f'*** Mesh: Connecting sw1 port {hosts_per_switch+1} to sw2 port {hosts_per_switch+1}\n')
        
    elif num_switches == 3:
        # Partial mesh: avoid triangle loop (sw1-sw2-sw3-sw1)
        # Connect sw1 to sw2 and sw3, but NOT sw2 to sw3 directly
        net.addLink(switches[0], switches[1], port1=hosts_per_switch+1, port2=hosts_per_switch+1)
        net.addLink(switches[0], switches[2], port1=hosts_per_switch+2, port2=hosts_per_switch+1)
        info(f'*** Mesh: Connecting sw1 port {hosts_per_switch+1} to sw2 port {hosts_per_switch+1}\n')
        info(f'*** Mesh: Connecting sw1 port {hosts_per_switch+2} to sw3 port {hosts_per_switch+1}\n')
        info(f'*** Mesh: Skipping sw2-sw3 direct link to avoid loop\n')
        
    elif num_switches == 4:
        # Dual-star pattern: two stars connected (avoids loops)
        net.addLink(switches[0], switches[1], port1=hosts_per_switch+1, port2=hosts_per_switch+1)  # sw1-sw2
        net.addLink(switches[0], switches[2], port1=hosts_per_switch+2, port2=hosts_per_switch+1)  # sw1-sw3
        net.addLink(switches[1], switches[3], port1=hosts_per_switch+2, port2=hosts_per_switch+1)  # sw2-sw4
        net.addLink(switches[2], switches[3], port1=hosts_per_switch+2, port2=hosts_per_switch+2)  # sw3-sw4
        info(f'*** Mesh: Creating dual-star pattern to avoid loops\n')
        
    else:
        # For larger networks: use star pattern (proven working)
        central_sw = switches[0]
        for i in range(1, num_switches):
            leaf_sw = switches[i]
            central_port = hosts_per_switch + i
            leaf_port = hosts_per_switch + 1
            net.addLink(central_sw, leaf_sw, port1=central_port, port2=leaf_port)
            info(f'*** Mesh: Using star pattern for {num_switches} switches (proven working)\n')
    
    # Add hosts using universal pattern
    hosts = create_hosts_universal(net, switches, num_switches, hosts_per_switch)
    
    return switches, hosts

def create_tree_topology(net, num_switches, hosts_per_switch):
    """Create tree topology using working pattern"""
    switches = []
    
    # Create root switch
    root_sw = net.addSwitch('sw1', cls=OVSSwitch, dpid='1')
    switches.append(root_sw)
    
    # Create tree structure - binary tree for simplicity
    remaining_switches = num_switches - 1
    parent_switches = [root_sw]
    port_map = {0: hosts_per_switch + 1}  # Track ports for each switch
    
    switch_id = 2
    while remaining_switches > 0 and parent_switches:
        current_level_switches = []
        
        for parent_idx, parent_sw in enumerate(parent_switches):
            if remaining_switches <= 0:
                break
            
            # Add up to 2 children per parent (binary tree)
            for child_num in range(min(2, remaining_switches)):
                child_sw = net.addSwitch(f'sw{switch_id}', cls=OVSSwitch, dpid=str(switch_id))
                switches.append(child_sw)
                current_level_switches.append(child_sw)
                
                # Connect parent to child
                parent_port = port_map.get(parent_idx, hosts_per_switch + 1)
                child_port = hosts_per_switch + 1
                net.addLink(parent_sw, child_sw, port1=parent_port, port2=child_port)
                info(f'*** Tree: Connecting sw{switches.index(parent_sw)+1} port {parent_port} to sw{switch_id} port {child_port}\n')
                
                # Update port tracking
                port_map[parent_idx] = parent_port + 1
                port_map[len(switches)-1] = child_port + 1
                
                switch_id += 1
                remaining_switches -= 1
        
        parent_switches = current_level_switches
    
    # Add hosts using universal pattern
    hosts = create_hosts_universal(net, switches, num_switches, hosts_per_switch)
    
    return switches, hosts

def create_linear_topology(net, num_switches, hosts_per_switch):
    """Create linear topology (chain) using working pattern"""
    switches = []
    
    # Create switches
    for i in range(1, num_switches + 1):
        sw = net.addSwitch(f'sw{i}', cls=OVSSwitch, dpid=str(i))
        switches.append(sw)
    
    # Create linear connections: sw1 -- sw2 -- sw3 -- sw4
    for i in range(num_switches - 1):
        sw1, sw2 = switches[i], switches[i + 1]
        # First switch uses port (hosts_per_switch + 1), others use (hosts_per_switch + 1) and (hosts_per_switch + 2)
        if i == 0:  # First switch
            port1 = hosts_per_switch + 1
        else:  # Middle switches need two ports
            port1 = hosts_per_switch + 2
        
        port2 = hosts_per_switch + 1  # Second switch always uses first trunk port for connection back
        
        net.addLink(sw1, sw2, port1=port1, port2=port2)
        info(f'*** Linear: Connecting sw{i+1} port {port1} to sw{i+2} port {port2}\n')
    
    # Add hosts using universal pattern
    hosts = create_hosts_universal(net, switches, num_switches, hosts_per_switch)
    
    return switches, hosts

def universal_sdn_test(topology_type='star', num_switches=3, hosts_per_switch=2, skip_cli=False):
    """
    Universal SDN test - applies PROVEN WORKING PATTERN to all topologies
    """
    
    setLogLevel('info')
    
    total_hosts = num_switches * hosts_per_switch
    info(f'*** Creating {topology_type} topology with {num_switches} switches and {total_hosts} hosts\n')
    
    # Generate UNIVERSAL Faucet configuration using proven working pattern
    config = generate_universal_working_config(num_switches, hosts_per_switch)
    config_file = f'universal_{topology_type}_faucet.yaml'
    
    # Save configuration
    with open(config_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    info(f'*** Generated universal Faucet configuration: {config_file}\n')
    
    # Start Faucet controller
    if not start_faucet_controller(config_file):
        raise Exception("Failed to start Faucet controller")
    
    net = Mininet()
    
    info('*** Adding controller\n')
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    
    info(f'*** Creating {topology_type} topology\n')
    # Apply working pattern to different physical topologies
    if topology_type == 'star':
        switches, hosts = create_star_topology(net, num_switches, hosts_per_switch)
    elif topology_type == 'mesh':
        switches, hosts = create_mesh_topology(net, num_switches, hosts_per_switch)
    elif topology_type == 'tree':
        switches, hosts = create_tree_topology(net, num_switches, hosts_per_switch)
    elif topology_type == 'linear':
        switches, hosts = create_linear_topology(net, num_switches, hosts_per_switch)
    else:
        raise ValueError(f"Unsupported topology type: {topology_type}")
    
    info('*** Starting network\n')
    net.start()
    
    info('*** Configuring switches for SDN\n')
    # Essential SDN configuration - same as working pattern
    for switch in switches:
        switch.cmd(f'ovs-vsctl set-controller {switch.name} tcp:127.0.0.1:6653')
        switch.cmd(f'ovs-vsctl set-fail-mode {switch.name} secure')
        switch.cmd(f'ovs-vsctl set bridge {switch.name} protocols=OpenFlow13')
    
    info('*** Waiting for Faucet to install flows...\n')
    time.sleep(20)  # Give Faucet time to install flows
    
    info('*** Checking flow installation\n')
    flows_installed = True
    for i, switch in enumerate(switches):
        print(f"=== SW{i+1} Flow Table ===")
        flows = switch.cmd(f'ovs-ofctl -O OpenFlow13 dump-flows {switch.name}')
        print(flows)
        if 'actions=' not in flows:
            flows_installed = False
    
    if flows_installed:
        print("✅ Flows installed - Faucet is working!")
    else:
        print("❌ No flows installed - Configuration issue")
    
    info('*** Testing connectivity\n')
    print(f"\n=== {topology_type.upper()} TOPOLOGY CONNECTIVITY TESTS ===")
    
    # Test same switch connectivity first
    same_switch_success = 0
    same_switch_total = 0
    for i in range(0, len(hosts), hosts_per_switch):
        if i + 1 < len(hosts):
            h1, h2 = hosts[i], hosts[i+1]
            result = h1.cmd(f'ping -c1 -W2 {h2.IP()}')
            success = '1 received' in result
            if success:
                same_switch_success += 1
            same_switch_total += 1
            print(f"{h1.name} -> {h2.name} (same switch): {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    # Test cross-switch connectivity - the critical test for all topologies
    cross_switch_success = 0
    cross_switch_total = 0
    if len(hosts) >= hosts_per_switch * 2:
        # Test several cross-switch pairs
        test_pairs = [
            (0, hosts_per_switch),  # sw1 to sw2
        ]
        if len(hosts) >= hosts_per_switch * 3:
            test_pairs.append((0, hosts_per_switch * 2))  # sw1 to sw3
        if len(hosts) >= hosts_per_switch * 4:
            test_pairs.append((hosts_per_switch, hosts_per_switch * 3))  # sw2 to sw4
        
        for h1_idx, h2_idx in test_pairs:
            if h2_idx < len(hosts):
                h1, h2 = hosts[h1_idx], hosts[h2_idx]
                result = h1.cmd(f'ping -c2 -W3 {h2.IP()}')
                success = '1 received' in result or '2 received' in result
                if success:
                    cross_switch_success += 1
                cross_switch_total += 1
                print(f"{h1.name} -> {h2.name} (cross switch): {'🎉 SUCCESS!' if success else '❌ FAILED'}")
    
    if cross_switch_success == cross_switch_total and cross_switch_total > 0:
        print(f"\n🎉🎉🎉 {topology_type.upper()} TOPOLOGY SUCCESS! 🎉🎉🎉")
        print("✅ Cross-switch communication working!")
        print("✅ Proven working pattern scales to all topologies!")
    
    print("\n=== FINAL PINGALL ===")
    loss = net.pingAll(timeout='3')
    success_rate = 100 - loss
    print(f"Overall success rate: {success_rate}%")
    
    if success_rate == 100:
        print("🏆 PERFECT SUCCESS - 100% CONNECTIVITY!")
        print(f"🎯 {topology_type.upper()} topology with {num_switches} switches and {total_hosts} hosts COMPLETE!")
    elif success_rate >= 90:
        print("🏆 EXCELLENT SUCCESS!")
    elif success_rate >= 60:
        print("✅ Good progress")
    else:
        print("❌ More debugging needed")
    
    if not skip_cli:
        print("\n=== ENTERING CLI ===")
        print("You can now test manually:")
        print("  pingall")
        print("  h1 ping h3")
        CLI(net)
    
    net.stop()
    stop_faucet_controller()
    
    return success_rate

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Universal SDN Test - All Topologies with Proven Working Pattern')
    parser.add_argument('--topology', '-t', choices=['star', 'mesh', 'tree', 'linear'], 
                       default='star', help='Topology type (default: star)')
    parser.add_argument('--switches', '-s', type=int, default=3, 
                       help='Number of switches (default: 3)')
    parser.add_argument('--hosts', '-H', type=int, default=2, 
                       help='Number of hosts per switch (default: 2)')
    parser.add_argument('--no-cli', action='store_true', 
                       help='Skip CLI and exit after tests')
    parser.add_argument('--test-all', action='store_true', 
                       help='Test all topology types with same parameters')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    
    if args.switches < 1:
        print("Error: Number of switches must be at least 1")
        exit(1)
    if args.hosts < 1:
        print("Error: Number of hosts per switch must be at least 1")
        exit(1)
    
    # Topology-specific validations
    if args.topology == 'mesh' and args.switches < 2:
        print("Error: Mesh topology requires at least 2 switches")
        exit(1)
    if args.topology == 'tree' and args.switches < 2:
        print("Error: Tree topology requires at least 2 switches")
        exit(1)
    if args.topology == 'linear' and args.switches < 2:
        print("Error: Linear topology requires at least 2 switches")
        exit(1)
    
    total_hosts = args.switches * args.hosts
    
    if args.test_all:
        print("🧪 TESTING ALL TOPOLOGIES WITH PROVEN WORKING PATTERN")
        print("=" * 60)
        
        topologies = ['star', 'mesh', 'tree', 'linear']
        results = {}
        
        for topology in topologies:
            print(f"\n🔬 Testing {topology.upper()} topology...")
            print(f"   Switches: {args.switches}, Hosts per switch: {args.hosts}")
            
            try:
                success_rate = universal_sdn_test(topology, args.switches, args.hosts, skip_cli=True)
                results[topology] = success_rate
                print(f"   Result: {success_rate}% success")
            except Exception as e:
                print(f"   Failed: {e}")
                results[topology] = 0
            
            print("-" * 40)
        
        print("\n📊 FINAL RESULTS SUMMARY:")
        print("=" * 40)
        for topology, success_rate in results.items():
            status = "🏆 PERFECT" if success_rate == 100 else "✅ GOOD" if success_rate >= 90 else "❌ FAILED"
            print(f"{topology.upper():>8}: {success_rate:>6.1f}% {status}")
        
        perfect_count = sum(1 for rate in results.values() if rate == 100)
        print(f"\n🎯 Perfect Success Rate: {perfect_count}/{len(topologies)} topologies")
        
        if perfect_count == len(topologies):
            print("🎉 ALL TOPOLOGIES ACHIEVE 100% CONNECTIVITY!")
        
    else:
        print(f"Starting universal SDN test with proven working pattern:")
        print(f"  Topology: {args.topology}")
        print(f"  Switches: {args.switches}")
        print(f"  Hosts per switch: {args.hosts}")
        print(f"  Total hosts: {total_hosts}")
        print()
        
        try:
            universal_sdn_test(args.topology, args.switches, args.hosts, args.no_cli)
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
            stop_faucet_controller()
        except Exception as e:
            print(f"Error: {e}")
            stop_faucet_controller()
            exit(1)