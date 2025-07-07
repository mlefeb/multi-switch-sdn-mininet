# Critical Fix: IP Address Conflicts and Routing

## Root Cause Identified

The inter-VLAN routing failure was caused by **IP address conflicts** between hosts and Faucet gateway interfaces.

### Before Fix:
- **h1**: `10.0.1.1/24` ❌ (conflicts with gateway)
- **h4**: `10.0.2.1/24` ❌ (conflicts with gateway)
- **Faucet gateways**: `10.0.1.1`, `10.0.2.1` ❌ (same as hosts)

### After Fix:
- **h1**: `10.0.1.2/24` ✅ (no conflict)
- **h4**: `10.0.2.2/24` ✅ (no conflict)  
- **Faucet gateways**: `10.0.1.1`, `10.0.2.1` ✅ (unique)

## Changes Made

### 1. Fixed Host IP Assignment
**File**: `definitive_test.py` lines 374, 407, 431
```python
# OLD: Conflicting IPs
host = net.addHost(f'h{host_num}', ip=f'10.0.{i}.{j}/24')

# NEW: Non-conflicting IPs
host_ip = j + 1  # j=1 becomes .2, j=2 becomes .3, etc.
host = net.addHost(f'h{host_num}', ip=f'10.0.{i}.{host_ip}/24')
```

### 2. Added Default Routes
**File**: `definitive_test.py` lines 547-554
```python
# Configure default routes for inter-VLAN routing
for i, host in enumerate(hosts):
    subnet_num = (i // hosts_per_switch) + 1
    gateway_ip = f'10.0.{subnet_num}.1'
    host.cmd(f'ip route add default via {gateway_ip}')
```

## Expected Results

With these fixes:
- **No IP conflicts** between hosts and gateways
- **Proper default routing** to enable inter-VLAN communication
- **100% connectivity** across all topologies

### New IP Scheme:
- **h1**: `10.0.1.2/24` → gateway: `10.0.1.1`
- **h2**: `10.0.1.3/24` → gateway: `10.0.1.1`  
- **h3**: `10.0.1.4/24` → gateway: `10.0.1.1`
- **h4**: `10.0.2.2/24` → gateway: `10.0.2.1`
- **h5**: `10.0.2.3/24` → gateway: `10.0.2.1`
- **h6**: `10.0.2.4/24` → gateway: `10.0.2.1`

This should resolve the inter-VLAN routing failure and achieve the required 100% connectivity across all three topologies (star, mesh, tree).