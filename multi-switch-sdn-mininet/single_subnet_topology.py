#!/usr/bin/env python3

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink
import time

def create_single_subnet_topology():
    """
    Create a 5-switch topology with 10 hosts all in the same subnet (10.0.0.0/8)
    This should make pingall work since it's all L2 switching within one subnet
    """
    
    net = Mininet(
        controller=RemoteController,
        switch=OVSSwitch,
        link=TCLink,
        autoSetMacs=True
    )
    
    info('*** Adding controller\n')
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    
    info('*** Adding switches\n')
    sw1 = net.addSwitch('sw1', dpid='0000000000000001', protocols='OpenFlow13')
    sw2 = net.addSwitch('sw2', dpid='0000000000000002', protocols='OpenFlow13') 
    sw3 = net.addSwitch('sw3', dpid='0000000000000003', protocols='OpenFlow13')
    sw4 = net.addSwitch('sw4', dpid='0000000000000004', protocols='OpenFlow13')
    sw5 = net.addSwitch('sw5', dpid='0000000000000005', protocols='OpenFlow13')
    
    info('*** Adding hosts in single subnet 10.0.0.0/8\n')
    h1 = net.addHost('h1', ip='10.0.1.10/8')
    h2 = net.addHost('h2', ip='10.0.1.20/8')
    h3 = net.addHost('h3', ip='10.0.2.10/8')
    h4 = net.addHost('h4', ip='10.0.2.20/8')
    h5 = net.addHost('h5', ip='10.0.3.10/8')
    h6 = net.addHost('h6', ip='10.0.3.20/8')
    h7 = net.addHost('h7', ip='10.0.4.10/8')
    h8 = net.addHost('h8', ip='10.0.4.20/8')
    h9 = net.addHost('h9', ip='10.0.5.10/8')
    h10 = net.addHost('h10', ip='10.0.5.20/8')
    
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
    
    # Create inter-switch links (connected topology)
    net.addLink(sw1, sw2, port1=3, port2=3)
    net.addLink(sw1, sw3, port1=4, port2=3)
    net.addLink(sw2, sw4, port1=4, port2=3)
    net.addLink(sw3, sw5, port1=4, port2=3)
    net.addLink(sw4, sw5, port1=4, port2=4)
    
    info('*** Starting network\n')
    net.start()
    
    info('*** Configuring switches for OpenFlow\n')
    # Configure switches to use OpenFlow and connect to controller
    for switch in [sw1, sw2, sw3, sw4, sw5]:
        switch.cmd('ovs-vsctl set-fail-mode %s secure' % switch.name)
        switch.cmd('ovs-vsctl set-controller %s tcp:127.0.0.1:6653' % switch.name)
        switch.cmd('ovs-vsctl set bridge %s protocols=OpenFlow13' % switch.name)
    
    info('*** Waiting for controller connection...\n')
    time.sleep(15)  # Give more time for switches to connect
    
    info('*** Checking switch connections\n')
    for switch in [sw1, sw2, sw3, sw4, sw5]:
        result = switch.cmd('ovs-vsctl show')
        if 'is_connected: true' in result:
            info(f'{switch.name}: Connected to controller\n')
        else:
            info(f'{switch.name}: NOT connected to controller\n')
    
    info('*** Testing connectivity\n')
    result = net.pingAll()
    
    if result == 0:
        info('*** SUCCESS: All hosts can communicate! SDN is working.\n')
        info('*** This proves 5-switch SDN network works across the topology.\n')
    else:
        info(f'*** Partial connectivity: {100-result:.1f}% success rate\n')
    
    info('*** Testing specific cross-switch pings\n')
    info('h1 (sw1) -> h5 (sw3): ')
    h1.cmd('ping -c1 10.0.3.10')
    info('h2 (sw1) -> h9 (sw5): ')
    h2.cmd('ping -c1 10.0.5.10')
    
    info('*** Network topology:\n')
    info('SW1: h1(10.0.1.10), h2(10.0.1.20)\n')
    info('SW2: h3(10.0.2.10), h4(10.0.2.20)\n')
    info('SW3: h5(10.0.3.10), h6(10.0.3.20)\n')
    info('SW4: h7(10.0.4.10), h8(10.0.4.20)\n')
    info('SW5: h9(10.0.5.10), h10(10.0.5.20)\n')
    info('All in subnet: 10.0.0.0/8\n')
    
    info('*** Running CLI (try: pingall, iperf h1 h9)\n')
    CLI(net)
    
    info('*** Stopping network\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    create_single_subnet_topology()