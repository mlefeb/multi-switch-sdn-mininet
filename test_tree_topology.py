#!/usr/bin/env python3

"""
Test tree topology structure to ensure all switches are connected
"""

def test_binary_tree_structure():
    """Test the binary tree structure for 20 switches"""
    
    print("🌳 TESTING BINARY TREE STRUCTURE")
    print("=" * 40)
    
    num_switches = 20
    
    print(f"\n📊 Binary Tree for {num_switches} switches:")
    print("Parent -> Children mapping:")
    
    all_children = set()
    connections = []
    
    for i in range(1, num_switches + 1):
        left_child = 2 * i
        right_child = 2 * i + 1
        
        children = []
        if left_child <= num_switches:
            children.append(left_child)
            all_children.add(left_child)
            connections.append((i, left_child, "left"))
        
        if right_child <= num_switches:
            children.append(right_child)
            all_children.add(right_child)
            connections.append((i, right_child, "right"))
        
        if children:
            print(f"   SW{i} -> {children}")
        else:
            print(f"   SW{i} -> [] (leaf)")
    
    print(f"\n🔍 Connectivity Analysis:")
    print(f"   Total switches: {num_switches}")
    print(f"   Switches with children: {len([i for i in range(1, num_switches + 1) if 2*i <= num_switches])}")
    print(f"   Total connections: {len(connections)}")
    print(f"   All children connected: {len(all_children)}")
    
    # Check if all switches except root have a parent
    root_switch = 1
    connected_switches = {root_switch}  # Root is always connected
    connected_switches.update(all_children)
    
    print(f"   Connected switches: {len(connected_switches)}")
    
    if len(connected_switches) == num_switches:
        print("   ✅ All switches are connected in the tree")
    else:
        missing = set(range(1, num_switches + 1)) - connected_switches
        print(f"   ❌ Missing switches: {missing}")
    
    print(f"\n📋 Expected Connection Log:")
    for parent, child, side in connections:
        parent_port = 3 if side == "left" else 4  # hosts_per_switch + 1 or 2
        child_port = 3
        print(f"   Tree: sw{parent} port {parent_port} to sw{child} port {child_port} ({side} child)")
    
    print(f"\n🎯 EXPECTED RESULT:")
    if len(connected_switches) == num_switches:
        print("✅ Tree topology should connect all 20 switches")
        print("✅ All switches should get flows from Faucet")
        print("✅ Should achieve 100% connectivity")
    else:
        print("❌ Tree topology has connection gaps")
        print(f"❌ Switches {missing} will be isolated")

if __name__ == '__main__':
    test_binary_tree_structure()