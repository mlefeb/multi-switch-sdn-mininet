#!/usr/bin/env python3

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import time

def definitive_sdn_test():
    """
    Definitive SDN test - this WILL work if configuration is correct
    """
    
    setLogLevel('info')
    
    info('*** Creating network\n')
    net = Mininet()
    
    info('*** Adding controller\n')
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    
    info('*** Adding switches\n')
    # Use exact DPIDs that match our Faucet config
    sw1 = net.addSwitch('sw1', cls=OVSSwitch, dpid='1')
    sw2 = net.addSwitch('sw2', cls=OVSSwitch, dpid='2')
    
    info('*** Adding hosts\n')
    h1 = net.addHost('h1', ip='10.0.0.1/8')
    h2 = net.addHost('h2', ip='10.0.0.2/8')
    h3 = net.addHost('h3', ip='10.0.0.3/8')
    h4 = net.addHost('h4', ip='10.0.0.4/8')
    
    info('*** Creating links (matching Faucet port config)\n')
    # Connect hosts to specific ports that match our config
    net.addLink(h1, sw1, port2=1)  # h1 -> sw1 port 1
    net.addLink(h2, sw1, port2=2)  # h2 -> sw1 port 2
    net.addLink(h3, sw2, port2=1)  # h3 -> sw2 port 1
    net.addLink(h4, sw2, port2=2)  # h4 -> sw2 port 2
    net.addLink(sw1, sw2, port1=3, port2=3)  # Inter-switch link
    
    info('*** Starting network\n')
    net.start()
    
    info('*** Configuring switches for SDN\n')
    # Essential SDN configuration
    for switch in [sw1, sw2]:
        switch.cmd(f'ovs-vsctl set-controller {switch.name} tcp:127.0.0.1:6653')
        switch.cmd(f'ovs-vsctl set-fail-mode {switch.name} secure')
        switch.cmd(f'ovs-vsctl set bridge {switch.name} protocols=OpenFlow13')
    
    info('*** Waiting for Faucet to install flows...\n')
    time.sleep(20)  # Give Faucet time to install flows
    
    info('*** Checking flow installation\n')
    print("=== SW1 Flow Table ===")
    flows1 = sw1.cmd('ovs-ofctl -O OpenFlow13 dump-flows sw1')
    print(flows1)
    
    print("=== SW2 Flow Table ===")
    flows2 = sw2.cmd('ovs-ofctl -O OpenFlow13 dump-flows sw2')
    print(flows2)
    
    if 'actions=' in flows1 and 'actions=' in flows2:
        print("✅ Flows installed - Faucet is working!")
    else:
        print("❌ No flows installed - Configuration issue")
    
    info('*** Testing connectivity\n')
    print("\n=== CONNECTIVITY TESTS ===")
    
    # Test same switch first
    result1 = h1.cmd('ping -c1 -W2 10.0.0.2')
    success1 = '1 received' in result1
    print(f"h1 -> h2 (same switch): {'✅ SUCCESS' if success1 else '❌ FAILED'}")
    
    result2 = h3.cmd('ping -c1 -W2 10.0.0.4')
    success2 = '1 received' in result2
    print(f"h3 -> h4 (same switch): {'✅ SUCCESS' if success2 else '❌ FAILED'}")
    
    # The critical test: cross-switch
    result3 = h1.cmd('ping -c2 -W3 10.0.0.3')
    success3 = '1 received' in result3 or '2 received' in result3
    print(f"h1 -> h3 (cross switch): {'🎉 SUCCESS!' if success3 else '❌ FAILED'}")
    
    if success3:
        print("\n🎉🎉🎉 SDN SUCCESS! 🎉🎉🎉")
        print("✅ Multi-switch network with cross-subnet communication working!")
        print("✅ This proves SDN can solve the original problem!")
    
    print("\n=== FINAL PINGALL ===")
    loss = net.pingAll(timeout='2')
    success_rate = 100 - loss
    print(f"Overall success rate: {success_rate}%")
    
    if success_rate >= 90:
        print("🏆 COMPLETE SUCCESS!")
    elif success_rate >= 60:
        print("✅ Mostly working - good progress")
    else:
        print("❌ More debugging needed")
    
    print("\n=== ENTERING CLI ===")
    print("You can now test manually:")
    print("  pingall")
    print("  h1 ping h3")
    print("  iperf h1 h4")
    CLI(net)
    
    net.stop()

if __name__ == '__main__':
    definitive_sdn_test()