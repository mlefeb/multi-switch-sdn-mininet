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

def generate_working_config(num_switches, hosts_per_switch):
    """
    Generate Faucet config based on the EXACT working pattern from working_minimal.yaml
    """
    
    config = {
        'vlans': {
            100: {
                'description': 'default VLAN',
                'unicast_flood': True  # CRITICAL for cross-switch forwarding
            }
        },
        'dps': {}
    }
    
    # Generate switches following the exact working pattern
    for i in range(1, num_switches + 1):
        interfaces = {}
        
        # Host ports - each gets native_vlan: 100
        for port in range(1, hosts_per_switch + 1):
            host_num = (i-1) * hosts_per_switch + port
            interfaces[port] = {
                'description': f'h{host_num}',
                'native_vlan': 100
            }
        
        # Inter-switch ports - reserve ports after host ports for connections
        # Star topology: sw1 has connections to all other switches
        if i == 1:  # Central switch
            for j in range(2, num_switches + 1):
                trunk_port = hosts_per_switch + (j - 1)
                interfaces[trunk_port] = {
                    'description': f'inter-switch link to sw{j}',
                    'native_vlan': 100  # CRITICAL: use native_vlan, not tagged_vlans
                }
        else:  # Leaf switches - only connect back to sw1
            trunk_port = hosts_per_switch + 1
            interfaces[trunk_port] = {
                'description': 'inter-switch link to sw1',
                'native_vlan': 100  # CRITICAL: use native_vlan, not tagged_vlans
            }
        
        config['dps'][f'sw{i}'] = {
            'dp_id': i,  # Use integer dp_id like working pattern
            'hardware': 'Open vSwitch',
            'interfaces': interfaces
        }
    
    return config

def start_faucet_controller(config_file):
    """Start Faucet controller using Docker with specified config"""
    
    info('*** Starting Faucet controller with Docker...\n')
    
    # Cleanup any existing containers
    try:
        subprocess.run(['docker', 'stop', 'enhanced-faucet'], check=False, capture_output=True)
        subprocess.run(['docker', 'rm', 'enhanced-faucet'], check=False, capture_output=True)
        time.sleep(2)
    except:
        pass
    
    # Start Faucet with the generated configuration
    cmd = [
        'docker', 'run', '-d',
        '--name', 'enhanced-faucet',
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
        check_cmd = ['docker', 'ps', '--filter', 'name=enhanced-faucet', '--format', '{{.Status}}']
        check_result = subprocess.run(check_cmd, capture_output=True, text=True)
        
        if 'Up' in check_result.stdout:
            info('*** Faucet controller started successfully\n')
            return True
        else:
            logs_cmd = ['docker', 'logs', 'enhanced-faucet']
            logs_result = subprocess.run(logs_cmd, capture_output=True, text=True)
            info(f'*** Faucet failed to start. Logs:\n{logs_result.stdout}\n{logs_result.stderr}\n')
            return False
            
    except subprocess.CalledProcessError as e:
        info(f'*** Error starting Faucet container: {e}\n')
        info(f'*** Command was: {cmd}\n')
        info(f'*** stderr: {e.stderr}\n')
        return False

def stop_faucet_controller():
    """Stop Faucet controller container"""
    try:
        subprocess.run(['docker', 'stop', 'enhanced-faucet'], check=False, capture_output=True)
        subprocess.run(['docker', 'rm', 'enhanced-faucet'], check=False, capture_output=True)
    except:
        pass

def create_star_topology(net, num_switches, hosts_per_switch):
    """Create star topology with exact port mappings matching config"""
    switches = []
    hosts = []
    
    # Create switches
    for i in range(1, num_switches + 1):
        sw = net.addSwitch(f'sw{i}', cls=OVSSwitch, dpid=str(i))
        switches.append(sw)
    
    # Create star connections: all switches connect to sw1
    central_sw = switches[0]  # sw1
    for i in range(1, num_switches):  # sw2, sw3, sw4, ...
        leaf_sw = switches[i]
        # Central switch port: hosts_per_switch + i (sw1 uses port 3 for sw2, port 4 for sw3, etc.)
        central_port = hosts_per_switch + i
        # Leaf switch port: hosts_per_switch + 1 (each leaf uses same port number)
        leaf_port = hosts_per_switch + 1
        net.addLink(central_sw, leaf_sw, port1=central_port, port2=leaf_port)
        info(f'*** Connecting sw1 port {central_port} to sw{i+1} port {leaf_port}\n')
    
    # Add hosts - all in same subnet following working pattern
    for i in range(1, num_switches + 1):
        for j in range(1, hosts_per_switch + 1):
            host_num = (i-1) * hosts_per_switch + j
            # All hosts in same subnet (10.0.0.x) like working pattern
            host = net.addHost(f'h{host_num}', ip=f'10.0.0.{host_num}/8')
            hosts.append(host)
            # Connect to switch port j
            net.addLink(host, switches[i-1], port2=j)
            info(f'*** Connecting h{host_num} to sw{i} port {j}\n')
    
    return switches, hosts

def enhanced_working_test(num_switches=3, hosts_per_switch=2, skip_cli=False):
    """
    Enhanced SDN test - scales the proven working pattern
    """
    
    setLogLevel('info')
    
    total_hosts = num_switches * hosts_per_switch
    info(f'*** Creating star topology with {num_switches} switches and {total_hosts} hosts\n')
    
    # Generate Faucet configuration based on working pattern
    config = generate_working_config(num_switches, hosts_per_switch)
    config_file = 'enhanced_faucet.yaml'
    
    # Save configuration
    with open(config_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    info(f'*** Generated Faucet configuration: {config_file}\n')
    
    # Start Faucet controller
    if not start_faucet_controller(config_file):
        raise Exception("Failed to start Faucet controller")
    
    net = Mininet()
    
    info('*** Adding controller\n')
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    
    info('*** Creating star topology\n')
    switches, hosts = create_star_topology(net, num_switches, hosts_per_switch)
    
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
    print("\n=== CONNECTIVITY TESTS ===")
    
    # Test same switch connectivity first
    same_switch_tests = []
    for i in range(0, len(hosts), hosts_per_switch):
        if i + 1 < len(hosts):
            h1, h2 = hosts[i], hosts[i+1]
            result = h1.cmd(f'ping -c1 -W2 {h2.IP()}')
            success = '1 received' in result
            same_switch_tests.append(success)
            print(f"{h1.name} -> {h2.name} (same switch): {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    # Test cross-switch connectivity - the critical test
    cross_switch_tests = []
    if len(hosts) >= hosts_per_switch * 2:
        # Test h1 (sw1) -> h(first host on sw2)
        h1 = hosts[0]
        h_cross = hosts[hosts_per_switch]  # First host on second switch
        result = h1.cmd(f'ping -c2 -W3 {h_cross.IP()}')
        success = '1 received' in result or '2 received' in result
        cross_switch_tests.append(success)
        print(f"{h1.name} -> {h_cross.name} (cross switch): {'🎉 SUCCESS!' if success else '❌ FAILED'}")
        
        # Test another cross-switch pair if we have enough hosts
        if len(hosts) >= hosts_per_switch * 3:
            h_cross2 = hosts[hosts_per_switch * 2]  # First host on third switch
            result2 = h1.cmd(f'ping -c2 -W3 {h_cross2.IP()}')
            success2 = '1 received' in result2 or '2 received' in result2
            cross_switch_tests.append(success2)
            print(f"{h1.name} -> {h_cross2.name} (cross switch): {'🎉 SUCCESS!' if success2 else '❌ FAILED'}")
    
    if all(cross_switch_tests):
        print("\n🎉🎉🎉 SDN SUCCESS! 🎉🎉🎉")
        print("✅ Multi-switch network with cross-switch communication working!")
        print("✅ This proves the scaling works!")
    
    print("\n=== FINAL PINGALL ===")
    loss = net.pingAll(timeout='3')
    success_rate = 100 - loss
    print(f"Overall success rate: {success_rate}%")
    
    if success_rate == 100:
        print("🏆 PERFECT SUCCESS - 100% CONNECTIVITY!")
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

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Enhanced SDN Test - Scaling the Working Pattern')
    parser.add_argument('--switches', '-s', type=int, default=3, 
                       help='Number of switches (default: 3)')
    parser.add_argument('--hosts', '-H', type=int, default=2, 
                       help='Number of hosts per switch (default: 2)')
    parser.add_argument('--no-cli', action='store_true', 
                       help='Skip CLI and exit after tests')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    
    if args.switches < 1:
        print("Error: Number of switches must be at least 1")
        exit(1)
    if args.hosts < 1:
        print("Error: Number of hosts per switch must be at least 1")
        exit(1)
    
    total_hosts = args.switches * args.hosts
    print(f"Starting enhanced working SDN test:")
    print(f"  Switches: {args.switches}")
    print(f"  Hosts per switch: {args.hosts}")
    print(f"  Total hosts: {total_hosts}")
    print()
    
    try:
        enhanced_working_test(args.switches, args.hosts, args.no_cli)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        stop_faucet_controller()
    except Exception as e:
        print(f"Error: {e}")
        stop_faucet_controller()
        exit(1)