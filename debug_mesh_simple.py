#!/usr/bin/env python3

"""
Simple mesh topology debug - create minimal mesh and test
"""

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.log import setLogLevel, info
import time

def simple_mesh_test():
    """
    Create simple 3-switch mesh and test basic connectivity
    """
    
    setLogLevel('info')
    
    info('*** Creating simple mesh test\n')
    net = Mininet()
    
    # Create controller (assume working Faucet is running)
    info('*** Adding controller\n')
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    
    info('*** Adding switches\n')
    sw1 = net.addSwitch('sw1', cls=OVSSwitch, dpid='1')
    sw2 = net.addSwitch('sw2', cls=OVSSwitch, dpid='2') 
    sw3 = net.addSwitch('sw3', cls=OVSSwitch, dpid='3')
    switches = [sw1, sw2, sw3]
    
    info('*** Adding hosts\n')
    h1 = net.addHost('h1', ip='10.0.0.1/8')
    h2 = net.addHost('h2', ip='10.0.0.2/8')
    h3 = net.addHost('h3', ip='10.0.0.3/8')
    h4 = net.addHost('h4', ip='10.0.0.4/8')
    h5 = net.addHost('h5', ip='10.0.0.5/8')
    h6 = net.addHost('h6', ip='10.0.0.6/8')
    hosts = [h1, h2, h3, h4, h5, h6]
    
    info('*** Creating host links\n')
    # Connect hosts to switches (2 hosts per switch)
    net.addLink(h1, sw1, port2=1)  # h1 -> sw1 port 1
    net.addLink(h2, sw1, port2=2)  # h2 -> sw1 port 2
    net.addLink(h3, sw2, port2=1)  # h3 -> sw2 port 1  
    net.addLink(h4, sw2, port2=2)  # h4 -> sw2 port 2
    net.addLink(h5, sw3, port2=1)  # h5 -> sw3 port 1
    net.addLink(h6, sw3, port2=2)  # h6 -> sw3 port 2
    
    info('*** Creating mesh links\n')
    # Full mesh: each switch connects to every other switch
    net.addLink(sw1, sw2, port1=3, port2=3)  # sw1 port 3 <-> sw2 port 3
    net.addLink(sw1, sw3, port1=4, port2=3)  # sw1 port 4 <-> sw3 port 3  
    net.addLink(sw2, sw3, port1=4, port2=4)  # sw2 port 4 <-> sw3 port 4
    
    info('*** Starting network\n')
    net.start()
    
    info('*** Configuring switches for SDN\n')
    for switch in switches:
        switch.cmd(f'ovs-vsctl set-controller {switch.name} tcp:127.0.0.1:6653')
        switch.cmd(f'ovs-vsctl set-fail-mode {switch.name} secure')
        switch.cmd(f'ovs-vsctl set bridge {switch.name} protocols=OpenFlow13')
    
    info('*** Waiting for flows\n')
    time.sleep(20)
    
    info('*** Testing connectivity\n')
    print("\n=== MESH CONNECTIVITY TESTS ===")
    
    # Test same switch first
    result1 = h1.cmd('ping -c1 -W2 10.0.0.2')
    success1 = '1 received' in result1
    print(f"h1 -> h2 (same switch sw1): {'✅ SUCCESS' if success1 else '❌ FAILED'}")
    
    result2 = h3.cmd('ping -c1 -W2 10.0.0.4')  
    success2 = '1 received' in result2
    print(f"h3 -> h4 (same switch sw2): {'✅ SUCCESS' if success2 else '❌ FAILED'}")
    
    result3 = h5.cmd('ping -c1 -W2 10.0.0.6')
    success3 = '1 received' in result3
    print(f"h5 -> h6 (same switch sw3): {'✅ SUCCESS' if success3 else '❌ FAILED'}")
    
    # Test cross-switch (direct mesh connections)
    result4 = h1.cmd('ping -c2 -W3 10.0.0.3')  # sw1 -> sw2 (direct link)
    success4 = '1 received' in result4 or '2 received' in result4
    print(f"h1 -> h3 (sw1->sw2 direct): {'🎉 SUCCESS!' if success4 else '❌ FAILED'}")
    
    result5 = h1.cmd('ping -c2 -W3 10.0.0.5')  # sw1 -> sw3 (direct link)
    success5 = '1 received' in result5 or '2 received' in result5  
    print(f"h1 -> h5 (sw1->sw3 direct): {'🎉 SUCCESS!' if success5 else '❌ FAILED'}")
    
    result6 = h3.cmd('ping -c2 -W3 10.0.0.5')  # sw2 -> sw3 (direct link)
    success6 = '1 received' in result6 or '2 received' in result6
    print(f"h3 -> h5 (sw2->sw3 direct): {'🎉 SUCCESS!' if success6 else '❌ FAILED'}")
    
    # Full pingall test
    print("\n=== FULL PINGALL ===")
    loss = net.pingAll(timeout='2')
    success_rate = 100 - loss
    print(f"Overall success rate: {success_rate}%")
    
    if success_rate == 100:
        print("🏆 MESH TOPOLOGY PERFECT!")
    else:
        print(f"❌ Mesh failing - only {success_rate}%")
        
        # Debug: show flow tables
        print("\n=== FLOW TABLES DEBUG ===")
        for i, switch in enumerate(switches):
            print(f"SW{i+1} flows:")
            flows = switch.cmd('ovs-ofctl -O OpenFlow13 dump-flows sw{}'.format(i+1))
            print(flows[:200] + "..." if len(flows) > 200 else flows)
    
    net.stop()
    return success_rate

if __name__ == '__main__':
    simple_mesh_test()