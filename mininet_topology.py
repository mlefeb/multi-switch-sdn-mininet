#!/usr/bin/env python3

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink
import time

def create_sdn_topology():
    """
    Create a 5-switch topology with 10 hosts distributed across different IP ranges
    Topology: Star-like with interconnected switches
    """
    
    # Create network with remote controller
    net = Mininet(
        controller=RemoteController,
        switch=OVSSwitch,
        link=TCLink,
        autoSetMacs=True
    )
    
    info('*** Adding controller\n')
    # Connect to Faucet controller running in Docker
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    
    info('*** Adding switches\n')
    # Add 5 switches with specific datapath IDs matching faucet.yaml
    sw1 = net.addSwitch('sw1', dpid='0000000000000001')
    sw2 = net.addSwitch('sw2', dpid='0000000000000002') 
    sw3 = net.addSwitch('sw3', dpid='0000000000000003')
    sw4 = net.addSwitch('sw4', dpid='0000000000000004')
    sw5 = net.addSwitch('sw5', dpid='0000000000000005')
    
    info('*** Adding hosts with different IP ranges\n')
    # Add hosts with IP addresses matching the VLANs configured in Faucet
    h1 = net.addHost('h1', ip='10.0.1.10/24', defaultRoute='via 10.0.1.1')
    h2 = net.addHost('h2', ip='10.0.1.20/24', defaultRoute='via 10.0.1.1')
    h3 = net.addHost('h3', ip='10.0.2.10/24', defaultRoute='via 10.0.2.1')
    h4 = net.addHost('h4', ip='10.0.2.20/24', defaultRoute='via 10.0.2.1')
    h5 = net.addHost('h5', ip='10.0.3.10/24', defaultRoute='via 10.0.3.1')
    h6 = net.addHost('h6', ip='10.0.3.20/24', defaultRoute='via 10.0.3.1')
    h7 = net.addHost('h7', ip='10.0.4.10/24', defaultRoute='via 10.0.4.1')
    h8 = net.addHost('h8', ip='10.0.4.20/24', defaultRoute='via 10.0.4.1')
    h9 = net.addHost('h9', ip='10.0.5.10/24', defaultRoute='via 10.0.5.1')
    h10 = net.addHost('h10', ip='10.0.5.20/24', defaultRoute='via 10.0.5.1')
    
    info('*** Creating links\n')
    # Connect hosts to switches (2 hosts per switch)
    net.addLink(h1, sw1, port2=1)
    net.addLink(h2, sw1, port2=2)
    net.addLink(h3, sw2, port2=1)
    net.addLink(h4, sw2, port2=2)
    net.addLink(h5, sw3, port2=1)
    net.addLink(h6, sw3, port2=2)
    net.addLink(h7, sw4, port2=1)
    net.addLink(h8, sw4, port2=2)
    net.addLink(h9, sw5, port2=1)
    net.addLink(h10, sw5, port2=2)
    
    # Create inter-switch links to form a connected topology
    # sw1 connects to sw2 and sw3
    net.addLink(sw1, sw2, port1=3, port2=3)
    net.addLink(sw1, sw3, port1=4, port2=3)
    
    # sw2 connects to sw4
    net.addLink(sw2, sw4, port1=4, port2=3)
    
    # sw3 connects to sw5  
    net.addLink(sw3, sw5, port1=4, port2=3)
    
    # sw4 connects to sw5 (creates redundant path)
    net.addLink(sw4, sw5, port1=4, port2=4)
    
    info('*** Starting network\n')
    net.start()
    
    info('*** Waiting for controller connection...\n')
    time.sleep(10)  # Give time for controller to configure switches
    
    info('*** Testing connectivity\n')
    # Test basic connectivity
    info('Testing pingall:\n')
    result = net.pingAll()
    
    if result == 0:
        info('*** SUCCESS: All hosts can communicate across IP ranges!\n')
    else:
        info('*** Some connectivity issues detected\n')
    
    info('*** Running CLI\n')
    info('You can now test connectivity manually:\n')
    info('  - pingall: Test all-to-all connectivity\n')
    info('  - h1 ping h3: Test cross-subnet connectivity\n')
    info('  - iperf h1 h5: Test bandwidth across subnets\n')
    CLI(net)
    
    info('*** Stopping network\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    create_sdn_topology()