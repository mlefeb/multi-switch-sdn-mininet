#!/usr/bin/env python3

"""
Investigate Mininet switch types and port configurations
"""

from mininet.node import OVSSwitch, OVSBridge, IVSSwitch, UserSwitch
from mininet.net import Mininet
from mininet.log import setLogLevel
import subprocess

def investigate_switch_types():
    """Investigate different Mininet switch types and their port capabilities"""
    
    print("🔍 MININET SWITCH TYPES AND PORT CAPABILITIES")
    print("=" * 60)
    
    print("\n📋 AVAILABLE SWITCH TYPES:")
    print("=" * 30)
    
    print("\n1. 🔧 OVSSwitch (Open vSwitch) - Default")
    print("   - Most common SDN switch in Mininet")
    print("   - Supports OpenFlow 1.0, 1.1, 1.2, 1.3")
    print("   - Default port limit: ~254 ports")
    print("   - Configurable via OVS settings")
    
    print("\n2. 🌉 OVSBridge (Open vSwitch Bridge)")
    print("   - Similar to OVSSwitch but different mode")
    print("   - Can support more ports")
    print("   - Less OpenFlow features")
    
    print("\n3. 🔄 IVSSwitch (Indigo Virtual Switch)")
    print("   - Alternative SDN switch implementation")
    print("   - May have different port limits")
    print("   - Less commonly used")
    
    print("\n4. 👤 UserSwitch (User-space switch)")
    print("   - Software-only implementation")
    print("   - Potentially unlimited ports")
    print("   - Lower performance")
    
    print("\n🔧 OVS PORT CONFIGURATION OPTIONS:")
    print("=" * 40)
    
    print("\n1. 📊 Check Current OVS Limits:")
    print("   ovs-vsctl show")
    print("   ovs-vsctl list bridge")
    print("   ovs-ofctl show <switch>")
    
    print("\n2. ⚙️ Increase OVS Port Limits:")
    print("   # Method 1: Per bridge")
    print("   ovs-vsctl set bridge sw1 other-config:max-ports=64")
    print("   ")
    print("   # Method 2: Global OVS configuration")
    print("   echo 'other-config:max-ports=64' >> /etc/openvswitch/conf.db")
    print("   ")
    print("   # Method 3: Mininet switch creation")
    print("   net.addSwitch('sw1', cls=OVSSwitch, datapath='kernel', max_ports=64)")
    
    print("\n3. 🏗️ Alternative Switch Classes:")
    print("   # Use OVSBridge for more ports")
    print("   net.addSwitch('sw1', cls=OVSBridge)")
    print("   ")
    print("   # Use UserSwitch for unlimited ports") 
    print("   net.addSwitch('sw1', cls=UserSwitch)")
    
    print("\n🧪 TESTING DIFFERENT SWITCH TYPES:")
    print("=" * 40)
    
    # Test basic switch creation
    setLogLevel('warning')  # Reduce noise
    
    switch_types = [
        ('OVSSwitch', OVSSwitch),
        ('OVSBridge', OVSBridge),
        ('UserSwitch', UserSwitch),
    ]
    
    for name, switch_class in switch_types:
        try:
            print(f"\n✅ {name}:")
            net = Mininet()
            
            # Try to create switch with many ports
            sw = net.addSwitch('sw1', cls=switch_class)
            
            # Add multiple hosts to test port limits
            for i in range(20):
                host = net.addHost(f'h{i+1}')
                net.addLink(host, sw)
            
            print(f"   - Successfully created with 20 ports")
            print(f"   - Class: {switch_class.__name__}")
            
            net.stop()
            
        except Exception as e:
            print(f"❌ {name}: {str(e)}")
    
    print(f"\n🎯 RECOMMENDATIONS:")
    print("=" * 20)
    
    print("\n1. 🥇 BEST: Configure OVS for more ports")
    print("   - Keep using OVSSwitch (proven, reliable)")
    print("   - Just increase the port limit")
    print("   - Command: ovs-vsctl set bridge sw1 other-config:max-ports=64")
    
    print("\n2. 🥈 ALTERNATIVE: Use OVSBridge")
    print("   - Different OVS mode with potentially higher limits")
    print("   - Change: cls=OVSBridge in addSwitch()")
    
    print("\n3. 🥉 FALLBACK: Use UserSwitch")
    print("   - Software-only, unlimited ports")
    print("   - Lower performance, less features")
    
    print(f"\n💡 IMMEDIATE SOLUTION:")
    print("Update the sdn_multi_topology_test.py to configure OVS switches with more ports!")

def show_ovs_port_config():
    """Show how to configure OVS for more ports"""
    
    print(f"\n🔧 OVS PORT CONFIGURATION CODE:")
    print("=" * 35)
    
    print("""
# In sdn_multi_topology_test.py, modify switch creation:

# BEFORE (default):
sw = net.addSwitch(f'sw{i}', cls=OVSSwitch, dpid=str(i))

# AFTER (more ports):
sw = net.addSwitch(f'sw{i}', cls=OVSSwitch, dpid=str(i), 
                   protocols='OpenFlow13')

# Then after network start, configure each switch:
for switch in switches:
    switch.cmd('ovs-vsctl set bridge {} other-config:max-ports=64'.format(switch.name))
    """)
    
    print("This allows up to 64 ports per switch!")
    print("For 64 ports: 62 trunk connections + 2 host ports = supports 63 switches!")

if __name__ == '__main__':
    investigate_switch_types()
    show_ovs_port_config()