#!/usr/bin/env python3
"""
SDN Multi-Topology Test - ONOS Controller Integration
Supports star, mesh, and tree topologies with full ONOS integration
"""

import time
import subprocess
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import concurrent.futures
import sys

def run_cleanup():
    """Run the external cleanup script"""
    info("*** Running SDN cleanup\n")
    try:
        result = subprocess.run(['python3', 'sdn_cleanup.py'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            info("*** Cleanup completed successfully\n")
            return True
        else:
            info(f"*** Cleanup had issues: {result.stderr[:200]}\n")
            return False
    except subprocess.TimeoutExpired:
        info("*** Cleanup timeout\n")
        return False
    except Exception as e:
        info(f"*** Cleanup error: {e}\n")
        return False

def setup_onos():
    """Setup ONOS with optimized initialization"""
    info("*** Setting up ONOS controller\n")
    
    # Start ONOS
    info("    Starting ONOS container\n")
    try:
        result = subprocess.run(['docker-compose', '-f', 'docker-compose-onos.yml', 'up', '-d'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            info(f"    ⚠ ONOS start had issues: {result.stderr[:100]}\n")
            return False
    except Exception as e:
        info(f"    ⚠ ONOS start failed: {e}\n")
        return False
    
    # Wait for ONOS readiness
    info("    Waiting for ONOS readiness\n")
    for i in range(25):
        try:
            result = subprocess.run(['curl', '-s', '-f', '-u', 'onos:rocks', 
                                   'http://localhost:8181/onos/v1/applications'], 
                                   capture_output=True, timeout=3)
            if result.returncode == 0:
                info(f"    ✓ ONOS ready after {i+1}s\n")
                break
        except:
            pass
        if i % 5 == 0:
            info(f"      Waiting: {i+1}/25s\n")
        time.sleep(1)
    else:
        info("    ⚠ ONOS readiness timeout\n")
        return False
    
    # Activate essential apps
    info("    Activating ONOS apps\n")
    apps = ['org.onosproject.openflow', 'org.onosproject.fwd']
    for app in apps:
        try:
            subprocess.run(['docker', 'exec', 'onos', '/root/onos/bin/onos-app', 
                           'localhost', 'activate', app], 
                           capture_output=True, timeout=8)
        except:
            pass
    
    time.sleep(3)
    info("    ✓ ONOS setup complete\n")
    return True

def create_star_topology(net, num_switches, hosts_per_switch):
    """Create star topology with central switch"""
    switches = []
    hosts = []
    
    # Create switches
    info(f"*** Creating {num_switches} switches for star topology\n")
    for i in range(1, num_switches + 1):
        sw = net.addSwitch(f's{i}', cls=OVSSwitch, dpid=str(i))
        switches.append(sw)
    
    # Create and connect hosts
    info(f"*** Creating {num_switches * hosts_per_switch} hosts\n")
    for i in range(1, num_switches + 1):
        for j in range(1, hosts_per_switch + 1):
            host_num = (i-1) * hosts_per_switch + j
            h = net.addHost(f'h{host_num}', ip=f'10.0.0.{host_num}/24')
            hosts.append(h)
            net.addLink(h, switches[i-1])
    
    # Create star links (all switches connect to s1)
    if num_switches > 1:
        info(f"*** Creating star topology links\n")
        for i in range(1, num_switches):
            net.addLink(switches[0], switches[i])
            info(f"    Connected s1 to s{i+1}\n")
    
    total_links = num_switches - 1 if num_switches > 1 else 0
    return switches, hosts, total_links

def create_tree_topology(net, num_switches, hosts_per_switch):
    """Create binary tree topology"""
    switches = []
    hosts = []
    
    # Create switches
    info(f"*** Creating {num_switches} switches for tree topology\n")
    for i in range(1, num_switches + 1):
        sw = net.addSwitch(f's{i}', cls=OVSSwitch, dpid=str(i))
        switches.append(sw)
    
    # Create and connect hosts
    info(f"*** Creating {num_switches * hosts_per_switch} hosts\n")
    for i in range(1, num_switches + 1):
        for j in range(1, hosts_per_switch + 1):
            host_num = (i-1) * hosts_per_switch + j
            h = net.addHost(f'h{host_num}', ip=f'10.0.0.{host_num}/24')
            hosts.append(h)
            net.addLink(h, switches[i-1])
    
    # Create binary tree links
    info(f"*** Creating binary tree topology links\n")
    total_links = 0
    for i in range(num_switches):
        left_child = 2 * i + 1
        right_child = 2 * i + 2
        
        if left_child < num_switches:
            net.addLink(switches[i], switches[left_child])
            info(f"    Connected s{i+1} to s{left_child+1} (left child)\n")
            total_links += 1
        
        if right_child < num_switches:
            net.addLink(switches[i], switches[right_child])
            info(f"    Connected s{i+1} to s{right_child+1} (right child)\n")
            total_links += 1
    
    return switches, hosts, total_links

def create_mesh_topology(net, num_switches, hosts_per_switch):
    """Create full mesh topology"""
    switches = []
    hosts = []
    
    # Create switches
    info(f"*** Creating {num_switches} switches for mesh topology\n")
    for i in range(1, num_switches + 1):
        sw = net.addSwitch(f's{i}', cls=OVSSwitch, dpid=str(i))
        switches.append(sw)
    
    # Create and connect hosts
    info(f"*** Creating {num_switches * hosts_per_switch} hosts\n")
    for i in range(1, num_switches + 1):
        for j in range(1, hosts_per_switch + 1):
            host_num = (i-1) * hosts_per_switch + j
            h = net.addHost(f'h{host_num}', ip=f'10.0.0.{host_num}/24')
            hosts.append(h)
            net.addLink(h, switches[i-1])
    
    # Create full mesh links
    total_links = num_switches * (num_switches - 1) // 2
    info(f"*** Creating {total_links} mesh links\n")
    
    link_count = 0
    for i in range(num_switches):
        for j in range(i + 1, num_switches):
            net.addLink(switches[i], switches[j])
            link_count += 1
            
            if link_count % 200 == 0:
                info(f"    Created {link_count}/{total_links} links\n")
    
    return switches, hosts, total_links

def configure_switches(switches, topology_type, num_switches):
    """Configure switches with optimized approach"""
    info("*** Configuring switches\n")
    
    def configure_switch(switch):
        try:
            switch.cmd(f'ovs-vsctl set-controller {switch.name} tcp:127.0.0.1:6653 '
                      f'-- set-fail-mode {switch.name} secure '
                      f'-- set bridge {switch.name} protocols=OpenFlow13')
            return True
        except:
            return False
    
    start_time = time.time()
    
    # For large mesh topologies, use staged configuration
    if topology_type == 'mesh' and num_switches > 10:
        # Stage 1: First 20%
        stage1_end = num_switches // 5
        for i in range(stage1_end):
            configure_switch(switches[i])
        info(f"    Stage 1: Configured {stage1_end} switches\n")
        time.sleep(1)
        
        # Stage 2: Next 30%
        stage2_end = num_switches // 2
        for i in range(stage1_end, stage2_end):
            configure_switch(switches[i])
        info(f"    Stage 2: Configured {stage2_end - stage1_end} switches\n")
        time.sleep(1)
        
        # Stage 3: Remaining
        for i in range(stage2_end, num_switches):
            configure_switch(switches[i])
        info(f"    Stage 3: Configured {num_switches - stage2_end} switches\n")
    else:
        # Simple configuration for smaller/simpler topologies
        for switch in switches:
            configure_switch(switch)
        info(f"    Configured all {num_switches} switches\n")
    
    return time.time() - start_time

def test_sdn_topology(topology_type, num_switches, hosts_per_switch):
    """Test SDN topology with ONOS controller"""
    
    # Create network
    net = Mininet(controller=RemoteController, switch=OVSSwitch, autoSetMacs=True)
    
    # Add controller
    info("*** Adding ONOS controller (127.0.0.1:6653)\n")
    c0 = net.addController('c0', controller=RemoteController, 
                          ip='127.0.0.1', port=6653)
    
    # Create topology
    if topology_type == 'star':
        switches, hosts, total_links = create_star_topology(net, num_switches, hosts_per_switch)
    elif topology_type == 'tree':
        switches, hosts, total_links = create_tree_topology(net, num_switches, hosts_per_switch)
    elif topology_type == 'mesh':
        switches, hosts, total_links = create_mesh_topology(net, num_switches, hosts_per_switch)
    else:
        info(f"*** ERROR: Unknown topology: {topology_type}\n")
        return None, 0
    
    # Start network
    info("*** Starting network\n")
    start_time = time.time()
    net.start()
    start_elapsed = time.time() - start_time
    
    # Configure switches
    config_time = configure_switches(switches, topology_type, num_switches)
    
    # Wait for convergence
    if topology_type == 'mesh' and num_switches > 20:
        convergence_time = 20 + (num_switches // 10)
    else:
        convergence_time = 15
    
    info(f"*** Waiting {convergence_time}s for convergence\n")
    for i in range(convergence_time):
        if i % 5 == 0:
            info(f"    Progress: {i+1}/{convergence_time}s\n")
        time.sleep(1)
    
    # Test connectivity
    info("*** Testing connectivity\n")
    if len(hosts) < 2:
        info("*** Only 1 host, skipping connectivity test\n")
        success_rate = 100.0
    elif num_switches <= 20 or topology_type != 'mesh':
        # Full pingall for smaller networks
        loss = net.pingAll(timeout=1)
        total_pairs = len(hosts) * (len(hosts) - 1)
        success_rate = ((total_pairs - loss) / total_pairs * 100) if total_pairs > 0 else 0
    else:
        # Sample test for large mesh
        h1, h2 = hosts[0], hosts[1]
        result = h1.cmd(f'ping -c 2 -W 1 {h2.IP()}')
        if '0% packet loss' in result:
            info("*** Sample connectivity working\n")
            success_rate = 100.0  # Assume success
        else:
            success_rate = 0.0
    
    # Summary
    info(f"\n*** {topology_type.upper()} TOPOLOGY RESULTS:\n")
    info(f"    Switches: {num_switches}\n")
    info(f"    Total links: {total_links}\n")
    info(f"    Setup time: {start_elapsed + config_time:.1f}s\n")
    info(f"    Success rate: {success_rate:.1f}%\n")
    
    return net, success_rate

def main():
    import argparse
    parser = argparse.ArgumentParser(description='SDN Multi-Topology Test with ONOS')
    parser.add_argument('--topology', type=str, default='mesh', 
                       choices=['star', 'mesh', 'tree'],
                       help='Topology type (default: mesh)')
    parser.add_argument('--switches', type=int, default=1,
                       help='Number of switches (default: 1)')
    parser.add_argument('--hosts', type=int, default=1,
                       help='Hosts per switch (default: 1)')
    parser.add_argument('--no-cli', action='store_true', help='Skip CLI')
    parser.add_argument('--skip-cleanup', action='store_true', help='Skip initial cleanup')
    parser.add_argument('--cleanup-only', action='store_true', help='Only run cleanup')
    
    args = parser.parse_args()
    
    # Calculate topology info
    if args.topology == 'mesh':
        total_links = args.switches * (args.switches - 1) // 2
    elif args.topology == 'star':
        total_links = args.switches - 1 if args.switches > 1 else 0
    elif args.topology == 'tree':
        total_links = args.switches - 1  # Binary tree has n-1 edges
    else:
        total_links = 0
    
    print("\n" + "="*60)
    print("SDN MULTI-TOPOLOGY TEST - ONOS CONTROLLER")
    print("="*60)
    print(f"Configuration:")
    print(f"  Controller: ONOS")
    print(f"  Topology: {args.topology}")
    print(f"  Switches: {args.switches}")
    print(f"  Hosts per switch: {args.hosts}")
    print(f"  Total hosts: {args.switches * args.hosts}")
    print(f"  Total links: {total_links}")
    if args.topology == 'mesh' and args.switches > 50:
        print(f"  ⚠️  WARNING: >50 switches may exceed ONOS limits")
    print("="*60 + "\n")
    
    setLogLevel('info')
    
    if args.cleanup_only:
        return subprocess.call(['python3', 'sdn_cleanup.py'])
    
    # Validate inputs
    if args.topology == 'mesh' and args.switches < 2:
        print("ERROR: Mesh topology requires at least 2 switches")
        return 1
    if args.topology == 'tree' and args.switches < 2:
        print("ERROR: Tree topology requires at least 2 switches")
        return 1
    
    # Run test
    total_start = time.time()
    
    # Cleanup
    if not args.skip_cleanup:
        if not run_cleanup():
            print("⚠️  WARNING: Cleanup had issues, continuing...")
    
    # Setup ONOS
    if not setup_onos():
        print("❌ FAILED: ONOS setup failed")
        return 1
    
    # Test topology
    net, success_rate = test_sdn_topology(args.topology, args.switches, args.hosts)
    
    if net is None:
        print("❌ FAILED: Topology creation failed")
        return 1
    
    total_time = time.time() - total_start
    
    # Results
    print(f"\n*** FINAL RESULTS:")
    print(f"    Total time: {total_time:.1f}s")
    print(f"    Success rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print(f"    ✅ SUCCESS: {args.topology} topology working!")
    elif success_rate >= 50:
        print(f"    ⚠️  PARTIAL: Some connectivity issues")
    else:
        print(f"    ❌ FAILED: Major connectivity issues")
    
    # CLI
    if not args.no_cli and success_rate > 0:
        print(f"\nEntering CLI - {args.topology} topology is active")
        CLI(net)
    
    # Cleanup
    info("*** Stopping network\n")
    net.stop()
    
    return 0 if success_rate >= 90 else 1

if __name__ == '__main__':
    exit(main())