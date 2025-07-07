#!/usr/bin/env python3

"""
Find the exact switch limit that causes failures
"""

import subprocess
import time

def test_switch_limit():
    """Test different switch counts to find the limit"""
    
    print("🔍 FINDING EXACT SWITCH LIMIT")
    print("=" * 35)
    
    test_counts = [10, 12, 14, 15, 16, 18, 20]
    
    for count in test_counts:
        print(f"\n🧪 Testing {count} switches:")
        
        try:
            # Quick test with linear topology (most reliable)
            cmd = [
                'sudo', 'python3', 'sdn_multi_topology_test.py',
                '--topology', 'linear',
                '--switches', str(count),
                '--hosts', '2',
                '--no-cli'
            ]
            
            print(f"   Running: {' '.join(cmd)}")
            
            # Run with timeout
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            
            # Parse output for failed switches
            output = result.stdout + result.stderr
            
            if '⚠️  Switches with no flows:' in output:
                # Extract failed switches
                for line in output.split('\n'):
                    if '⚠️  Switches with no flows:' in line:
                        failed = line.split(':')[1].strip()
                        print(f"   ❌ Failed switches: {failed}")
                        break
            elif 'Overall success rate: ' in output:
                # Extract success rate
                for line in output.split('\n'):
                    if 'Overall success rate: ' in line:
                        rate = line.split(':')[1].strip()
                        print(f"   ✅ Success rate: {rate}")
                        break
            else:
                print(f"   ⚠️  Unclear result")
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout after 3 minutes")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print(f"   Sleeping 5s before next test...")
        time.sleep(5)
    
    print(f"\n🎯 ANALYSIS:")
    print("Look for the pattern:")
    print("- ✅ X switches: All working")
    print("- ❌ X+1 switches: Some failures")
    print("This will tell us the exact limit!")

if __name__ == '__main__':
    test_switch_limit()