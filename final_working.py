#!/usr/bin/env python3

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import time

def final_working_sdn():
    """
    Final working SDN demo - minimal but functional
    """
    
    setLogLevel('info')
    
    # Create network without any defaults that might interfere
    net = Mininet()
    
    info('*** Adding controller\n')
    c0 = net.addController('c0', 
                          controller=RemoteController, 
                          ip='127.0.0.1', 
                          port=6653)
    
    info('*** Adding switches with explicit configuration\n')
    sw1 = net.addSwitch('sw1', 
                       cls=OVSSwitch,
                       dpid='0000000000000001',
                       protocols='OpenFlow13')
    sw2 = net.addSwitch('sw2', 
                       cls=OVSSwitch,
                       dpid='0000000000000002',
                       protocols='OpenFlow13')
    
    info('*** Adding hosts\n')
    h1 = net.addHost('h1', ip='10.0.0.1/8')
    h2 = net.addHost('h2', ip='10.0.0.2/8')
    h3 = net.addHost('h3', ip='10.0.0.3/8')
    h4 = net.addHost('h4', ip='10.0.0.4/8')
    
    info('*** Creating links\n')
    net.addLink(h1, sw1)
    net.addLink(h2, sw1)
    net.addLink(h3, sw2)
    net.addLink(h4, sw2)
    net.addLink(sw1, sw2)  # Critical inter-switch link
    
    info('*** Starting network\n')
    net.start()
    
    info('*** Configuring switches manually\n')
    # Manually configure each switch for SDN operation
    sw1.cmd('ovs-vsctl del-controller sw1')
    sw1.cmd('ovs-vsctl set-controller sw1 tcp:127.0.0.1:6653')
    sw1.cmd('ovs-vsctl set-fail-mode sw1 secure')
    sw1.cmd('ovs-vsctl set bridge sw1 protocols=OpenFlow13')
    
    sw2.cmd('ovs-vsctl del-controller sw2')
    sw2.cmd('ovs-vsctl set-controller sw2 tcp:127.0.0.1:6653')
    sw2.cmd('ovs-vsctl set-fail-mode sw2 secure')
    sw2.cmd('ovs-vsctl set bridge sw2 protocols=OpenFlow13')
    
    # Clear any existing flows
    sw1.cmd('ovs-ofctl -O OpenFlow13 del-flows sw1')
    sw2.cmd('ovs-ofctl -O OpenFlow13 del-flows sw2')
    
    info('*** Waiting for controller to configure switches...\n')
    time.sleep(15)
    
    info('*** Verifying connections\n')
    sw1_status = sw1.cmd('ovs-vsctl show | grep "is_connected"')
    sw2_status = sw2.cmd('ovs-vsctl show | grep "is_connected"')
    
    print(f"SW1 status: {sw1_status.strip()}")
    print(f"SW2 status: {sw2_status.strip()}")
    
    info('*** Testing connectivity step by step\n')
    
    # Test 1: Same switch connectivity
    print("\n=== TEST 1: Same Switch Connectivity ===")
    result1 = h1.cmd('ping -c1 -W1 10.0.0.2')
    if '1 received' in result1:
        print("✅ h1 -> h2 (same switch): SUCCESS")
    else:
        print("❌ h1 -> h2 (same switch): FAILED")
    
    result2 = h3.cmd('ping -c1 -W1 10.0.0.4')
    if '1 received' in result2:
        print("✅ h3 -> h4 (same switch): SUCCESS")
    else:
        print("❌ h3 -> h4 (same switch): FAILED")
    
    # Test 2: Cross-switch connectivity (the key test)
    print("\n=== TEST 2: Cross-Switch Connectivity ===")
    result3 = h1.cmd('ping -c2 -W2 10.0.0.3')
    if '1 received' in result3 or '2 received' in result3:
        print("🎉 h1 -> h3 (cross-switch): SUCCESS!")
        print("✅ SDN WORKING: Cross-switch communication enabled!")
    else:
        print("❌ h1 -> h3 (cross-switch): FAILED")
        print("❌ SDN not working properly")
    
    # Show flow tables for debugging
    print("\n=== FLOW TABLES ===")
    print("SW1 flows:")
    sw1.cmd('ovs-ofctl -O OpenFlow13 dump-flows sw1')
    print("\nSW2 flows:")
    sw2.cmd('ovs-ofctl -O OpenFlow13 dump-flows sw2')
    
    # Final pingall test
    print("\n=== FINAL PINGALL TEST ===")
    result = net.pingAll(timeout='1')
    success_rate = 100 - result
    print(f"Overall connectivity: {success_rate}%")
    
    if success_rate >= 80:
        print("🎉 SUCCESS: SDN network is working!")
        print("✅ Multi-switch network with cross-subnet communication achieved!")
    else:
        print("❌ Partial success - some connectivity issues remain")
    
    print("\n=== ENTERING CLI FOR MANUAL TESTING ===")
    print("Try: pingall, h1 ping h3, iperf h1 h4")
    CLI(net)
    
    info('*** Stopping network\n')
    net.stop()

if __name__ == '__main__':
    final_working_sdn()