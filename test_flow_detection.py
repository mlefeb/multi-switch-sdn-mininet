#!/usr/bin/env python3

"""
Test programmatic flow detection instead of arbitrary wait times
"""

import time
import re

def check_flows_installed(switch, min_flows=1):
    """
    Check if flows are installed on a switch
    Returns (flows_installed, flow_count, sample_flows)
    """
    try:
        # Get flows from switch
        flows_output = switch.cmd(f'ovs-ofctl -O OpenFlow13 dump-flows {switch.name}')
        
        # Parse flows - exclude default drop rules and table stats
        flow_lines = []
        for line in flows_output.split('\n'):
            line = line.strip()
            # Look for actual flow rules (contain actions= and not just drop)
            if 'actions=' in line and 'drop' not in line.lower() and 'cookie=' in line:
                flow_lines.append(line)
        
        flow_count = len(flow_lines)
        flows_installed = flow_count >= min_flows
        
        return flows_installed, flow_count, flow_lines[:3]  # Return first 3 flows as samples
        
    except Exception as e:
        return False, 0, [f"Error: {e}"]

def wait_for_flows_installed(switches, max_wait_time=120, check_interval=2):
    """
    Wait for flows to be installed on all switches
    Returns (success, total_time, switch_status)
    """
    
    print(f"🔍 WAITING FOR FLOWS TO BE INSTALLED...")
    print(f"   Max wait time: {max_wait_time}s")
    print(f"   Check interval: {check_interval}s")
    print(f"   Target switches: {len(switches)}")
    
    start_time = time.time()
    switch_status = {}
    
    while time.time() - start_time < max_wait_time:
        elapsed = time.time() - start_time
        print(f"\n⏱️  Check at {elapsed:.1f}s:")
        
        all_switches_ready = True
        switches_with_flows = 0
        
        for i, switch in enumerate(switches):
            switch_name = f"SW{i+1}"
            
            if switch_name not in switch_status or not switch_status[switch_name]['ready']:
                flows_installed, flow_count, sample_flows = check_flows_installed(switch, min_flows=1)
                
                switch_status[switch_name] = {
                    'ready': flows_installed,
                    'flow_count': flow_count,
                    'sample_flows': sample_flows,
                    'check_time': elapsed
                }
                
                if flows_installed:
                    print(f"   ✅ {switch_name}: {flow_count} flows installed")
                    switches_with_flows += 1
                else:
                    print(f"   ⏳ {switch_name}: No flows yet")
                    all_switches_ready = False
            else:
                # Already ready
                switches_with_flows += 1
        
        print(f"   Progress: {switches_with_flows}/{len(switches)} switches ready")
        
        if all_switches_ready:
            total_time = time.time() - start_time
            print(f"\n🎉 ALL FLOWS INSTALLED in {total_time:.1f}s!")
            return True, total_time, switch_status
        
        # Wait before next check
        time.sleep(check_interval)
    
    # Timeout reached
    total_time = time.time() - start_time
    print(f"\n⏰ TIMEOUT after {total_time:.1f}s")
    return False, total_time, switch_status

def test_flow_detection_concept():
    """Test the flow detection concept with mock data"""
    
    print("🧪 TESTING FLOW DETECTION CONCEPT")
    print("=" * 40)
    
    # Mock flow outputs for testing
    mock_flows = {
        'no_flows': 'NXST_FLOW reply (xid=0x4):\n',
        'with_flows': '''NXST_FLOW reply (xid=0x4):
 cookie=0x5adc15c0, duration=10.123s, table=0, n_packets=0, n_bytes=0, priority=4096,in_port="sw1-eth1",vlan_tci=0x0000/0x1fff actions=push_vlan:0x8100,set_field:4196->vlan_vid,goto_table:1
 cookie=0x5adc15c0, duration=10.123s, table=1, n_packets=0, n_bytes=0, priority=8191,in_port="sw1-eth1",dl_vlan=100,dl_src=aa:bb:cc:dd:ee:01 actions=goto_table:2
 cookie=0x5adc15c0, duration=10.123s, table=2, n_packets=0, n_bytes=0, priority=8192,dl_vlan=100,dl_dst=aa:bb:cc:dd:ee:01 actions=pop_vlan,output:"sw1-eth1"
'''
    }
    
    print("\n📊 MOCK FLOW PARSING TEST:")
    
    for scenario, output in mock_flows.items():
        print(f"\n{scenario}:")
        
        # Parse flows manually for testing
        flow_lines = []
        for line in output.split('\n'):
            line = line.strip()
            if 'actions=' in line and 'drop' not in line.lower() and 'cookie=' in line:
                flow_lines.append(line)
        
        flow_count = len(flow_lines)
        print(f"   Detected flows: {flow_count}")
        
        if flow_count > 0:
            print(f"   Sample flow: {flow_lines[0][:80]}...")
    
    print(f"\n🎯 EXPECTED BENEFITS:")
    print("1. ⚡ Faster convergence - no unnecessary waiting")
    print("2. 🎯 Reliable detection - wait for actual flows, not arbitrary time")
    print("3. 📊 Progress visibility - see switches come online one by one")
    print("4. 🛡️ Timeout protection - still have maximum wait time")
    print("5. 🔍 Debugging info - know exactly which switches are ready")
    
    print(f"\n💡 IMPLEMENTATION APPROACH:")
    print("Replace this code:")
    print("   time.sleep(flow_timeout)  # Arbitrary wait")
    print("")
    print("With this code:")
    print("   success, time_taken, status = wait_for_flows_installed(switches)")
    print("   if success:")
    print("       print(f'Flows ready in {time_taken:.1f}s')")

if __name__ == '__main__':
    test_flow_detection_concept()