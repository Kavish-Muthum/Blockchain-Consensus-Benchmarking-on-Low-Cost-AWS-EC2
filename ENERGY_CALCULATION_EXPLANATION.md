# Energy Calculation Explanation

## How Energy Usage is Calculated

### The Problem: Missing CloudWatch Metrics

Many benchmarks show **0.0 Joules** in raw logs because:
1. **CloudWatch Metrics Delay**: CloudWatch metrics have a 1-5 minute delay
2. **Empty Metrics**: Some benchmarks collected before metrics were available
3. **CPU Utilization = 0%**: When CloudWatch data is missing, CPU% defaults to 0

### The Solution: Estimated Energy Model

Energy is **recalculated during normalization** using an estimated model that accounts for:
- **Idle Power Consumption**: Instances consume power even when idle
- **Active Power Scaling**: Power increases with CPU utilization
- **TDP (Thermal Design Power)**: Maximum power consumption for each instance type

### Energy Calculation Formula

```python
# Base power consumption (TDP) from instance configuration
base_power_watts = instance_config["estimated_tdp_watts"]
# t4g.2xlarge (ARM): 24W
# t3.2xlarge (x86): 28W

# Idle power (30% of TDP) - instances consume this even at 0% CPU
idle_power_watts = base_power_watts * 0.30
# ARM: 24W * 0.30 = 7.2W
# x86: 28W * 0.30 = 8.4W

# Active power (70% of TDP) - scales with CPU utilization
active_power_watts = (base_power_watts * 0.70) * (cpu_utilization_percent / 100.0)
# At 0% CPU: 0W
# At 100% CPU: base_power_watts * 0.70

# Total power consumption
total_power_watts = idle_power_watts + active_power_watts

# Energy consumption (Joules = Watts × seconds)
energy_joules = total_power_watts * duration_seconds
# Duration: 300 seconds (5 minutes)
```

### Example Calculations

#### Example 1: ARM (t4g.2xlarge) - PoW Workload
- **TDP**: 24W
- **CPU Utilization**: 3.84% (from CloudWatch)
- **Duration**: 300 seconds

```
idle_power = 24W × 0.30 = 7.2W
active_power = (24W × 0.70) × (3.84% / 100%) = 16.8W × 0.0384 = 0.645W
total_power = 7.2W + 0.645W = 7.845W
energy = 7.845W × 300s = 2,353.5 Joules
```

**Result**: 2,353.7 Joules (matches actual calculation)

#### Example 2: ARM (t4g.2xlarge) - PoS Workload (No CloudWatch Data)
- **TDP**: 24W
- **CPU Utilization**: 0% (CloudWatch data missing, default to 0)
- **Duration**: 300 seconds

```
idle_power = 24W × 0.30 = 7.2W
active_power = (24W × 0.70) × (0% / 100%) = 0W
total_power = 7.2W + 0W = 7.2W
energy = 7.2W × 300s = 2,160 Joules
```

**Result**: 2,160 Joules (idle consumption only)

#### Example 3: x86 (t3.2xlarge) - BFT Workload (No CloudWatch Data)
- **TDP**: 28W
- **CPU Utilization**: 0% (CloudWatch data missing)
- **Duration**: 300 seconds

```
idle_power = 28W × 0.30 = 8.4W
active_power = (28W × 0.70) × (0% / 100%) = 0W
total_power = 8.4W + 0W = 8.4W
energy = 8.4W × 300s = 2,520 Joules
```

**Result**: 2,520 Joules (idle consumption only)

### Why Some Show 0 Joules in Raw Logs

Raw log files show `energy_joules: 0.0` for benchmarks where:
1. CloudWatch metrics were empty (not yet available)
2. CPU utilization defaulted to 0%
3. Original calculation failed: `0W × 300s = 0 Joules`

**BUT**: During normalization, energy is **recalculated** using the fixed formula above, which ensures:
- **Non-zero energy**: Even at 0% CPU, instances consume idle power
- **Consistent estimates**: All benchmarks use the same energy model
- **Realistic values**: Based on TDP and estimated idle consumption

### Final Energy Values (After Normalization)

All energy values in the final summary are **recalculated** during normalization, ensuring:
- ✅ Non-zero energy for all benchmarks (idle power included)
- ✅ Consistent energy model across all workloads
- ✅ Realistic estimates based on instance TDP

## Energy Efficiency Calculation

```
Energy Efficiency (Joules/work) = Total Energy (Joules) / Work Units Completed

Example: ARM PoW
Efficiency = 2,353.7 Joules / 162,809,595 hashes = 1.45 × 10⁻⁵ Joules/hash
```

Lower values = better energy efficiency (less energy per work unit)

## Why This Model is Used

1. **Cloud Limitation**: Cannot directly measure power consumption in cloud instances
2. **Standard Practice**: Energy estimation from CPU utilization + TDP is standard in cloud benchmarking
3. **Conservative Estimate**: 30% idle power is a conservative estimate (real idle may be higher)
4. **Consistency**: All benchmarks use the same model for fair comparison

## Limitations

1. **Estimated, Not Measured**: Energy is calculated, not directly measured
2. **Idle Power Assumption**: 30% idle power is an estimate (may vary)
3. **CloudWatch Delay**: Some benchmarks may have missed CPU metrics due to CloudWatch delay
4. **Burstable Instances**: t3/t4g instances use CPU credits, which may affect power consumption

