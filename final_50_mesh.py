#!/usr/bin/env python3
"""
Final 50-Switch Full Mesh - Based on working 3-switch test
With staged startup to prevent connection storms
"""

import time
import subprocess
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info

def create_50_switch_mesh():
    """Create 50-switch full mesh using exact working configuration"""
    
    setLogLevel('info')
    
    # Create network EXACTLY as the working 3-switch version
    net = Mininet(controller=RemoteController, switch=OVSSwitch, autoSetMacs=True)
    
    # Use EXACT controller configuration that worked
    info("*** Adding ONOS controller (172.20.0.11)\n")
    c0 = net.addController('c0', controller=RemoteController, 
                          ip='172.20.0.11', port=6653)
    
    switches = []
    hosts = []
    num_switches = 50
    
    # Create switches EXACTLY as working version
    info(f"*** Creating {num_switches} switches\n")
    for i in range(1, num_switches + 1):
        sw = net.addSwitch(f's{i}', cls=OVSSwitch, dpid=str(i))
        switches.append(sw)
    
    # Create hosts EXACTLY as working version
    info(f"*** Creating {num_switches} hosts\n")
    for i in range(1, num_switches + 1):
        h = net.addHost(f'h{i}', ip=f'10.0.0.{i}/24')
        hosts.append(h)
        net.addLink(h, switches[i-1])
    
    # Create FULL MESH topology
    total_links = num_switches * (num_switches - 1) // 2
    info(f"*** Creating {total_links} mesh links\n")
    
    link_count = 0
    for i in range(num_switches):
        for j in range(i + 1, num_switches):
            net.addLink(switches[i], switches[j])
            link_count += 1
            if link_count % 200 == 0:
                info(f"    Created {link_count}/{total_links} links\n")
    
    info(f"*** Created all {total_links} mesh links\n")
    
    # Start network with STAGED approach
    info("*** Starting network\n")
    net.start()
    
    # Configure switches in STAGES to prevent connection storm
    info("*** Configuring switches in stages\n")
    
    # Stage 1: First 10 switches
    info("*** Stage 1: Configuring switches 1-10\n")
    for i in range(10):
        switch = switches[i]
        switch.cmd(f'ovs-vsctl set-controller {switch.name} tcp:172.20.0.11:6653')
        switch.cmd(f'ovs-vsctl set-fail-mode {switch.name} secure')
        switch.cmd(f'ovs-vsctl set bridge {switch.name} protocols=OpenFlow13')
    time.sleep(5)
    
    # Stage 2: Switches 11-25
    info("*** Stage 2: Configuring switches 11-25\n")
    for i in range(10, 25):
        switch = switches[i]
        switch.cmd(f'ovs-vsctl set-controller {switch.name} tcp:172.20.0.11:6653')
        switch.cmd(f'ovs-vsctl set-fail-mode {switch.name} secure')
        switch.cmd(f'ovs-vsctl set bridge {switch.name} protocols=OpenFlow13')
    time.sleep(5)
    
    # Stage 3: Switches 26-50
    info("*** Stage 3: Configuring switches 26-50\n")
    for i in range(25, 50):
        switch = switches[i]
        switch.cmd(f'ovs-vsctl set-controller {switch.name} tcp:172.20.0.11:6653')
        switch.cmd(f'ovs-vsctl set-fail-mode {switch.name} secure')
        switch.cmd(f'ovs-vsctl set bridge {switch.name} protocols=OpenFlow13')
        if i % 5 == 0:
            time.sleep(1)  # Brief pause every 5 switches
    
    # Wait for ONOS convergence - longer for 50 switches
    info("*** Waiting 40s for ONOS to handle full mesh\n")
    for i in range(40):
        info(f"    Wait: {i+1}/40s\r")
        time.sleep(1)
    info("\n")
    
    # Test connectivity
    info("*** Testing connectivity\n")
    
    # First do a sample test
    info("*** Sample test: h1 -> h2\n")
    h1, h2 = hosts[0], hosts[1]
    result = h1.cmd(f'ping -c 3 -W 2 {h2.IP()}')
    if '0% packet loss' in result:
        info("*** Sample test PASSED\n")
        
        # Now do full pingall
        info("*** Running full pingall (this may take a while)\n")
        start_time = time.time()
        loss = net.pingAll(timeout=1)
        duration = time.time() - start_time
        
        total_pairs = len(hosts) * (len(hosts) - 1)
        success_rate = ((total_pairs - loss) / total_pairs * 100) if total_pairs > 0 else 0
        
        info(f"\n*** RESULTS:\n")
        info(f"    Test duration: {duration:.1f}s\n")
        info(f"    Success rate: {success_rate:.1f}%\n")
        info(f"    Failed pings: {loss} out of {total_pairs}\n")
        
        return net, success_rate
    else:
        info("*** Sample test FAILED - skipping full test\n")
        return net, 0

def main():
    print("\n" + "="*60)
    print("50-SWITCH FULL MESH - FINAL ATTEMPT")
    print("="*60)
    print("Based on working 3-switch configuration")
    print("Controller: ONOS at 172.20.0.11:6653")
    print("Topology: FULL MESH (1,225 links)")
    print("Approach: Staged switch configuration")
    print("="*60 + "\n")
    
    # Run test
    net, success_rate = create_50_switch_mesh()
    
    if success_rate >= 90:
        print(f"\n✅ SUCCESS: {success_rate:.1f}% connectivity achieved!")
        print("50-switch full mesh is working!")
    elif success_rate >= 50:
        print(f"\n⚠️  PARTIAL SUCCESS: {success_rate:.1f}% connectivity")
        print("ONOS may be hitting limits")
    else:
        print(f"\n❌ FAILED: Only {success_rate:.1f}% connectivity")
        print("50 switches may be too many for ONOS")
    
    # Always enter CLI to investigate
    CLI(net)
    
    # Cleanup
    net.stop()
    return 0

if __name__ == '__main__':
    exit(main())