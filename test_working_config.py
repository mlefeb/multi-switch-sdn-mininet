#!/usr/bin/env python3

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import time
import subprocess

def test_working_faucet_config():
    """Test using the exact working faucet.yaml configuration"""
    
    setLogLevel('info')
    
    info('*** Creating network\n')
    net = Mininet()
    
    info('*** Adding controller\n')
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    
    info('*** Adding switches\n')
    # Use exact DPIDs from working faucet.yaml
    sw1 = net.addSwitch('sw1', cls=OVSSwitch, dpid='1')
    sw2 = net.addSwitch('sw2', cls=OVSSwitch, dpid='2')
    
    info('*** Adding hosts\n')
    # Use non-conflicting IPs (avoid .1 which is gateway)
    h1 = net.addHost('h1', ip='10.0.1.2/24')
    h2 = net.addHost('h2', ip='10.0.1.3/24')
    h3 = net.addHost('h3', ip='10.0.2.2/24')
    h4 = net.addHost('h4', ip='10.0.2.3/24')
    
    info('*** Creating links (matching faucet.yaml port config)\n')
    # Connect hosts to specific ports that match faucet.yaml
    net.addLink(h1, sw1, port2=1)  # h1 -> sw1 port 1 (subnet1)
    net.addLink(h2, sw1, port2=2)  # h2 -> sw1 port 2 (subnet1)
    net.addLink(h3, sw2, port2=1)  # h3 -> sw2 port 1 (subnet2)
    net.addLink(h4, sw2, port2=2)  # h4 -> sw2 port 2 (subnet2)
    net.addLink(sw1, sw2, port1=3, port2=3)  # Inter-switch link
    
    info('*** Starting network\n')
    net.start()
    
    info('*** Configuring switches for SDN\n')
    # Essential SDN configuration
    for switch in [sw1, sw2]:
        switch.cmd(f'ovs-vsctl set-controller {switch.name} tcp:127.0.0.1:6653')
        switch.cmd(f'ovs-vsctl set-fail-mode {switch.name} secure')
        switch.cmd(f'ovs-vsctl set bridge {switch.name} protocols=OpenFlow13')
    
    info('*** Configuring host routing\n')
    # Add default routes to gateways
    h1.cmd('ip route add default via 10.0.1.1')
    h2.cmd('ip route add default via 10.0.1.1')
    h3.cmd('ip route add default via 10.0.2.1')
    h4.cmd('ip route add default via 10.0.2.1')
    
    info('*** Waiting for Faucet to install flows...\n')
    time.sleep(20)  # Give Faucet time to install flows
    
    info('*** Testing connectivity\n')
    print("\\n=== CONNECTIVITY TESTS ===")
    
    # Test same subnet first
    result1 = h1.cmd('ping -c1 -W2 10.0.1.3')
    success1 = '1 received' in result1
    print(f"h1 -> h2 (same subnet): {'✅ SUCCESS' if success1 else '❌ FAILED'}")
    
    result2 = h3.cmd('ping -c1 -W2 10.0.2.3')
    success2 = '1 received' in result2
    print(f"h3 -> h4 (same subnet): {'✅ SUCCESS' if success2 else '❌ FAILED'}")
    
    # The critical test: cross-subnet (inter-VLAN routing)
    result3 = h1.cmd('ping -c2 -W3 10.0.2.2')
    success3 = '1 received' in result3 or '2 received' in result3
    print(f"h1 -> h3 (cross subnet): {'🎉 SUCCESS!' if success3 else '❌ FAILED'}")
    
    if success3:
        print("\\n🎉🎉🎉 INTER-VLAN ROUTING SUCCESS! 🎉🎉🎉")
        print("✅ Multi-subnet network with inter-VLAN routing working!")
    
    print("\\n=== FINAL PINGALL ===")
    loss = net.pingAll(timeout='3')
    success_rate = 100 - loss
    print(f"Overall success rate: {success_rate}%")
    
    if success_rate == 100:
        print("🏆 PERFECT SUCCESS - 100% CONNECTIVITY!")
    else:
        print(f"❌ {success_rate}% success rate")
    
    print("\\n=== ENTERING CLI ===")
    print("Available commands:")
    print("  pingall")
    print("  h1 ping h3")
    print("  h1 route")
    CLI(net)
    
    net.stop()

if __name__ == '__main__':
    print("Testing with working faucet.yaml configuration...")
    print("Make sure faucet.yaml is being used by the controller!")
    test_working_faucet_config()