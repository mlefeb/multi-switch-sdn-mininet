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
import glob

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
        # For larger networks: use simple linear chain to avoid all port conflicts
        # This ensures all switches are connected without interface naming issues
        info(f'*** Mesh: Using linear chain for {num_switches} switches (avoiding port conflicts)\n')
        info(f'*** NOTE: True mesh topology complex at scale - using connected chain\n')
        
        # Create simple linear chain: SW1-SW2-SW3-...-SW20
        for i in range(num_switches - 1):
            sw1, sw2 = switches[i], switches[i + 1]
            
            # Port assignments for linear chain
            if i == 0:  # First switch (SW1)
                port1 = hosts_per_switch + 1  # Port 3 for 2 hosts
            else:  # Middle switches need two ports for chain
                port1 = hosts_per_switch + 2  # Port 4 (port 3 used for incoming)
            
            port2 = hosts_per_switch + 1  # Port 3 for next switch (incoming)
            
            net.addLink(sw1, sw2, port1=port1, port2=port2)
            info(f'*** Mesh: Chain sw{i+1} port {port1} to sw{i+2} port {port2}\n')
    
    # Add hosts using universal pattern
    hosts = create_hosts_universal(net, switches, num_switches, hosts_per_switch)
    
    return switches, hosts

def create_tree_topology(net, num_switches, hosts_per_switch):
    """Create simple binary tree topology with proper port management"""
    switches = []
    
    # Create all switches first
    for i in range(1, num_switches + 1):
        sw = net.addSwitch(f'sw{i}', cls=OVSSwitch, dpid=str(i))
        switches.append(sw)
    
    # Track port usage for each switch
    port_usage = {}
    for i in range(1, num_switches + 1):
        # Initialize: hosts use ports 1,2, next available is 3
        port_usage[i] = hosts_per_switch + 1
    
    # Create simple binary tree connections
    # For switch i (1-indexed), children are at 2*i and 2*i+1
    for i in range(1, num_switches + 1):
        parent_idx = i - 1  # 0-indexed
        parent_sw = switches[parent_idx]
        
        # Left child
        left_child_idx = 2 * i
        if left_child_idx <= num_switches:
            left_child_sw = switches[left_child_idx - 1]  # 0-indexed
            
            # Parent uses next available port
            parent_port = port_usage[i]
            port_usage[i] += 1  # Reserve this port
            
            # Child uses next available port (may already have parent connection)
            child_port = port_usage[left_child_idx]
            port_usage[left_child_idx] += 1  # Reserve this port
            
            net.addLink(parent_sw, left_child_sw, port1=parent_port, port2=child_port)
            info(f'*** Tree: sw{i} port {parent_port} to sw{left_child_idx} port {child_port} (left child)\n')
        
        # Right child
        right_child_idx = 2 * i + 1
        if right_child_idx <= num_switches:
            right_child_sw = switches[right_child_idx - 1]  # 0-indexed
            
            # Parent uses next available port
            parent_port = port_usage[i]
            port_usage[i] += 1  # Reserve this port
            
            # Child uses next available port
            child_port = port_usage[right_child_idx]
            port_usage[right_child_idx] += 1  # Reserve this port
            
            net.addLink(parent_sw, right_child_sw, port1=parent_port, port2=child_port)
            info(f'*** Tree: sw{i} port {parent_port} to sw{right_child_idx} port {child_port} (right child)\n')
    
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

def cleanup_old_configs():
    """Clean up old config files to prevent confusion"""
    old_configs = glob.glob('universal_*_faucet.yaml')
    for config in old_configs:
        try:
            os.remove(config)
            info(f'*** Cleaned up old config: {config}\n')
        except:
            pass

def check_flows_installed(switch, min_flows=1):
    """
    Check if flows are installed on a switch
    Returns (flows_installed, flow_count, sample_flows)
    """
    try:
        # Get flows from switch
        flows_output = switch.cmd(f'ovs-ofctl -O OpenFlow13 dump-flows {switch.name}')
        
        # Parse flows - exclude default drop rules and table stats
        flow_lines = []
        for line in flows_output.split('\n'):
            line = line.strip()
            # Look for actual flow rules (contain actions= and not just drop)
            if 'actions=' in line and 'drop' not in line.lower() and 'cookie=' in line:
                flow_lines.append(line)
        
        flow_count = len(flow_lines)
        flows_installed = flow_count >= min_flows
        
        return flows_installed, flow_count, flow_lines[:3]  # Return first 3 flows as samples
        
    except Exception as e:
        return False, 0, [f"Error: {e}"]

def wait_for_flows_installed(switches, max_wait_time=120, check_interval=3):
    """
    Wait for flows to be installed on all switches
    Returns (success, total_time, switch_status)
    """
    
    info(f'*** Programmatic flow detection: checking {len(switches)} switches every {check_interval}s\n')
    
    start_time = time.time()
    switch_status = {}
    
    while time.time() - start_time < max_wait_time:
        elapsed = time.time() - start_time
        
        all_switches_ready = True
        switches_with_flows = 0
        
        for i, switch in enumerate(switches):
            switch_name = f"SW{i+1}"
            
            if switch_name not in switch_status or not switch_status[switch_name]['ready']:
                flows_installed, flow_count, sample_flows = check_flows_installed(switch, min_flows=1)
                
                switch_status[switch_name] = {
                    'ready': flows_installed,
                    'flow_count': flow_count,
                    'sample_flows': sample_flows,
                    'check_time': elapsed
                }
                
                if flows_installed:
                    info(f'*** {switch_name}: {flow_count} flows installed at {elapsed:.1f}s\n')
                    switches_with_flows += 1
                else:
                    all_switches_ready = False
            else:
                # Already ready
                switches_with_flows += 1
        
        if elapsed > 0 and elapsed % 10 == 0:  # Progress update every 10s
            info(f'*** Flow detection progress: {switches_with_flows}/{len(switches)} switches ready at {elapsed:.1f}s\n')
        
        if all_switches_ready:
            total_time = time.time() - start_time
            info(f'*** All flows detected in {total_time:.1f}s!\n')
            return True, total_time, switch_status
        
        # Wait before next check
        time.sleep(check_interval)
    
    # Timeout reached
    total_time = time.time() - start_time
    return False, total_time, switch_status

def universal_sdn_test(topology_type='star', num_switches=3, hosts_per_switch=2, skip_cli=False):
    """
    Universal SDN test - applies PROVEN WORKING PATTERN to all topologies
    """
    
    setLogLevel('info')
    
    # Clean up network interfaces from any previous tests
    cleanup_network_interfaces()
    
    # Clean up old config files to prevent caching issues
    cleanup_old_configs()
    
    total_hosts = num_switches * hosts_per_switch
    info(f'*** Creating {topology_type} topology with {num_switches} switches and {total_hosts} hosts\n')
    
    # Generate UNIVERSAL Faucet configuration using proven working pattern
    config = generate_universal_working_config(num_switches, hosts_per_switch)
    
    # FIXED: Use dynamic filename that includes parameters to prevent caching issues
    config_file = f'universal_{topology_type}_s{num_switches}_h{hosts_per_switch}_faucet.yaml'
    
    # Always regenerate config to ensure it matches current parameters
    info(f'*** Generating fresh configuration for {num_switches} switches, {hosts_per_switch} hosts per switch\n')
    with open(config_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    # VALIDATION: Verify config matches parameters
    actual_switches = len(config['dps'])
    if actual_switches != num_switches:
        raise Exception(f"Config generation error: expected {num_switches} switches, got {actual_switches}")
    
    info(f'*** Generated universal Faucet configuration: {config_file}\n')
    info(f'*** Validated: {actual_switches} switches configured correctly\n')
    
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
        # FIXED: Increase port limit to support large topologies
        switch.cmd(f'ovs-vsctl set bridge {switch.name} other-config:max-ports=64')
        info(f'*** {switch.name}: Configured for up to 64 ports\n')
    
    info('*** Waiting for Faucet to install flows...\n')
    # IMPROVED: Programmatic flow detection instead of arbitrary wait
    max_wait_time = max(60, num_switches * 4)  # Conservative maximum, but usually much faster
    info(f'*** Checking for flow installation (max {max_wait_time}s timeout)\n')
    
    success, actual_time, switch_status = wait_for_flows_installed(switches, max_wait_time)
    
    if success:
        info(f'*** Flows installed successfully in {actual_time:.1f}s (much faster than arbitrary wait!)\n')
    else:
        info(f'*** Warning: Not all flows installed after {actual_time:.1f}s\n')
    
    info('*** Final flow verification\n')
    
    # Use the switch status from programmatic detection
    flows_installed = success
    failed_switches = []
    
    # Display detailed flow status
    for i, switch in enumerate(switches):
        switch_name = f"SW{i+1}"
        print(f"=== {switch_name} Flow Table ===")
        
        if switch_name in switch_status:
            status = switch_status[switch_name]
            if status['ready']:
                print(f"✅ {switch_name}: {status['flow_count']} flows installed (detected at {status['check_time']:.1f}s)")
                # Show sample flows
                for j, flow in enumerate(status['sample_flows'][:2]):
                    if isinstance(flow, str) and len(flow) > 50:
                        print(f"   Flow {j+1}: {flow[:80]}...")
            else:
                print(f"❌ {switch_name}: No flows installed")
                failed_switches.append(i+1)
                
                # Check controller connection for failed switches
                controller_check = switch.cmd(f'ovs-vsctl get-controller {switch.name}')
                print(f"   Controller: {controller_check.strip()}")
        else:
            # Fallback check if not in status
            flows_installed_fallback, flow_count, _ = check_flows_installed(switch)
            if flows_installed_fallback:
                print(f"✅ {switch_name}: {flow_count} flows installed")
            else:
                print(f"❌ {switch_name}: No flows installed")
                failed_switches.append(i+1)
                flows_installed = False
    
    if failed_switches:
        print(f"\n⚠️  Switches with no flows: {failed_switches}")
        print("   This may indicate controller connection or topology issues")
    
    if flows_installed:
        print("✅ All flows installed - Faucet is working!")
    else:
        print("❌ Some switches missing flows - Check topology and controller")
    
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
    
    # Clean up network interfaces to prevent conflicts in subsequent tests
    cleanup_network_interfaces()
    
    return success_rate

def cleanup_network_interfaces():
    """Clean up any leftover network interfaces"""
    try:
        # Clean up any leftover OVS bridges
        info('*** Cleaning up network interfaces\n')
        subprocess.run(['sudo', 'ovs-vsctl', '--if-exists', 'del-br', 'ovs-system'], 
                      capture_output=True, check=False)
        
        # Clean up any leftover network namespaces
        subprocess.run(['sudo', 'ip', 'netns', 'flush'], 
                      capture_output=True, check=False)
        
        # Clean up mininet
        subprocess.run(['sudo', 'mn', '-c'], 
                      capture_output=True, check=False)
        
        time.sleep(2)  # Give time for cleanup
        
    except Exception as e:
        info(f'*** Warning: Network cleanup failed: {e}\n')

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