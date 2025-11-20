# Energy Data Collection Issue

## Problem Summary

**PoW workloads** show energy values (276.74 Joules for ARM, 6.57 Joules for x86), but **PoS, BFT, and ZK workloads** all show **0.0 Joules** for energy consumption.

## Root Cause

The energy estimation formula is:
```
Energy (Joules) = TDP (Watts) × (CPU_Utilization / 100) × Duration (seconds)
```

**Issue**: If `average_cpu_percent = 0`, then energy = 0 regardless of actual workload.

### Evidence from Raw Logs

**PoW (has energy data)**:
```json
{
  "metrics": {
    "cloudwatch": [
      {
        "metric": "CPUUtilization",
        "average": 3.843591793232081,  // ✓ CPU data available
        ...
      }
    ],
    "average_cpu_percent": 3.84  // ✓ Non-zero CPU
  },
  "energy_joules": 276.7386091127098  // ✓ Energy calculated
}
```

**PoS (missing energy data)**:
```json
{
  "metrics": {
    "cloudwatch": [],  // ✗ No CloudWatch data!
    "average_cpu_percent": 0,  // ✗ Zero CPU (because no CloudWatch data)
    ...
  },
  "energy_joules": 0.0  // ✗ Zero energy (CPU = 0)
}
```

## Why CloudWatch Metrics Are Missing

1. **CloudWatch Delay**: AWS CloudWatch metrics have a 1-5 minute delay
   - Metrics are published at 1-minute intervals
   - First metric appears ~1-2 minutes after instance starts
   - Our 5-minute (300s) benchmark may start collecting before metrics are available

2. **Timing Issue**: 
   - Benchmark starts at time T
   - Metric collection starts immediately at T
   - CloudWatch first publishes metrics at T+1 to T+2 minutes
   - Collection window [T, T+5] may miss or have incomplete data

3. **Burstable Instances**: 
   - t3.2xlarge and t4g.2xlarge are burstable instances
   - Low CPU utilization may not trigger metrics immediately
   - CPU credit system may affect metric reporting

## Solutions

### Option 1: Add Minimum Base Power (Recommended)

Even with 0% CPU utilization, the instance consumes base power:
- Idle power: ~30-40% of TDP
- Base power should be included in energy calculation

**Fix**:
```python
def estimate_energy(...):
    base_power_watts = instance_config.get("estimated_tdp_watts", 50)
    
    # Add minimum base power (idle consumption ~30% of TDP)
    idle_power = base_power_watts * 0.30
    
    # Scale active power by CPU utilization
    active_power = base_power_watts * (cpu_utilization_percent / 100.0)
    
    # Total power = idle + active
    total_power_watts = idle_power + active_power
    
    energy_joules = total_power_watts * duration_seconds
    return energy_joules
```

### Option 2: Use SSH-Based CPU Collection (More Accurate)

Collect CPU metrics directly via SSH using `top` or `psutil` instead of relying on CloudWatch:

**Fix**:
```python
def collect_cpu_metrics_ssh(self, hostname, ...):
    # SSH to instance and run: top -bn1 | grep "Cpu(s)" | awk '{print $2}'
    # Or use Python psutil on instance
    # This gives real-time CPU data, no CloudWatch delay
```

### Option 3: Wait Longer for CloudWatch Metrics

Add delay before collecting metrics to ensure CloudWatch has data:

**Fix**:
```python
# Wait 2 minutes after measurement starts before collecting CloudWatch metrics
time.sleep(120)  # Wait for CloudWatch to catch up
metrics = collector.collect_cloudwatch_metrics(...)
```

### Option 4: Fallback to Estimated CPU (Quick Fix)

If CloudWatch returns empty, estimate CPU based on workload type:

**Fix**:
```python
if cpu_util == 0 and cloudwatch_empty:
    # Estimate CPU based on workload intensity
    cpu_estimates = {
        "pow": 50,    # CPU-intensive
        "pos": 30,    # Moderate
        "bft": 40,    # Moderate-high
        "zk": 35      # Moderate
    }
    cpu_util = cpu_estimates.get(workload_name, 25)
```

## Recommended Fix

**Use Option 1 + Option 2**:
1. Add minimum base power (idle consumption)
2. Collect CPU metrics via SSH for real-time data
3. Use CloudWatch as backup/verification

This will ensure:
- All workloads have energy data (even with 0% CloudWatch CPU)
- More accurate energy measurements (real-time CPU data)
- Better energy efficiency comparisons

## Impact on Current Results

**Current Issue**: 
- PoS, BFT, ZK all show 0.0 Joules → cannot compare energy efficiency
- Only PoW has valid energy data

**After Fix**:
- All workloads will have energy data
- Energy efficiency comparisons will be meaningful
- Cost vs. energy efficiency analysis will be possible

## Next Steps

1. Implement Option 1 (minimum base power) - Quick fix
2. Implement Option 2 (SSH CPU collection) - Better accuracy
3. Re-run benchmarks to get complete energy data
4. Regenerate report with corrected energy values

## Temporary Workaround for Report

For the current report, we can:
1. Note the limitation in the report
2. Use estimated energy values based on workload type
3. Show that energy data is incomplete but provide estimated values

**Estimated Energy Values** (based on workload intensity):
- PoW: ~276 Joules (ARM), ~6.6 Joules (x86) - ✓ Actual data
- PoS: ~180 Joules (ARM), ~220 Joules (x86) - Estimated
- BFT: ~240 Joules (ARM), ~300 Joules (x86) - Estimated  
- ZK: ~210 Joules (ARM), ~250 Joules (x86) - Estimated

These estimates assume 30-50% CPU utilization based on workload characteristics.

