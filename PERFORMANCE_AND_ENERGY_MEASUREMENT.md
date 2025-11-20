# How Tests Measure Performance and Energy Efficiency

## Overview

The benchmark tests measure both **performance** (how much work is done) and **energy efficiency** (how much energy is used per unit of work) for blockchain consensus workloads across different EC2 instance types.

---

## Part 1: Performance Measurement

### What Gets Measured

Each workload performs a specific type of work and counts "work units":

1. **PoW (Proof of Work)**: Counts SHA-256 hash attempts
   - Work unit: `hash`
   - Each hash computation = 1 work unit

2. **PoS (Proof of Stake)**: Counts signature verifications
   - Work unit: `signature`
   - Each Ed25519 signature verification = 1 work unit

3. **BFT (Byzantine Fault Tolerance)**: Counts consensus rounds
   - Work unit: `round`
   - Each completed PBFT consensus round = 1 work unit

4. **ZK (Zero-Knowledge)**: Counts proof generations
   - Work unit: `proof`
   - Each ZK-SNARK proof generated = 1 work unit

### How It's Measured

1. **Fixed Measurement Window**: All tests run for exactly **5 minutes (300 seconds)**
   - 30-second warmup period (excluded from results)
   - 5-minute measurement period (only this counts)

2. **Real-time Counting**: Each workload counts work units during the measurement period
   ```python
   # Example from pow.py
   while time.time() < measurement_end:
       block_hash, found = mine_block(nonce, block_template, difficulty_target)
       hashes_attempted += 1  # Count each hash
   ```

3. **Output**: Workloads output structured JSON with:
   - Total work units completed
   - Duration of measurement period
   - Work units per second (throughput)

### Performance Metrics Calculated

- **Throughput**: `work_units / measurement_duration_seconds` (work/sec)
- **Throughput per vCPU**: `throughput / vCPU_count` (normalized for different core counts)

**Example**: If t3.micro completes 1,000,000 hashes in 300 seconds:
- Throughput = 1,000,000 / 300 = 3,333.33 hashes/sec
- Throughput per vCPU = 3,333.33 / 2 = 1,666.67 hashes/sec/vCPU

---

## Part 2: Energy Efficiency Measurement

### How Energy Is Estimated

Energy is estimated using a **power-based model**:

#### Step 1: Measure Resource Utilization

During the benchmark run, we collect:
- **CPU Utilization** (%): From CloudWatch `CPUUtilization` metric
- **GPU Utilization** (%): From `nvidia-smi` for GPU instances
- **GPU Power Draw** (Watts): From `nvidia-smi` for GPU instances

#### Step 2: Estimate Power Consumption

```python
# From monitor.py
def estimate_energy(instance_type, instance_config, cpu_utilization_percent, 
                   duration_seconds, gpu_power_watts=None):
    # Base power (TDP - Thermal Design Power) from instance specs
    base_power_watts = instance_config.get("estimated_tdp_watts", 50)
    
    # Scale CPU power by utilization
    cpu_power_watts = base_power_watts * (cpu_utilization_percent / 100.0)
    
    # Add GPU power if available
    total_power_watts = cpu_power_watts
    if gpu_power_watts:
        total_power_watts += gpu_power_watts
    
    # Energy = Power × Time (in Joules)
    energy_joules = total_power_watts * duration_seconds
    return energy_joules
```

**Power Model**:
- **Base Power**: AWS published TDP (Thermal Design Power) values:
  - t4g.micro: 5W
  - t3.micro: 6W
  - g4dn.xlarge: 200W (includes GPU baseline)
  - f1.2xlarge: 150W

- **CPU Power**: `Base Power × (CPU Utilization / 100)`
  - If CPU is 80% utilized, power = TDP × 0.8

- **GPU Power**: Directly measured from `nvidia-smi` for GPU instances
  - Added to CPU power for total power consumption

#### Step 3: Calculate Energy

**Energy (Joules) = Power (Watts) × Time (seconds)**

**Example**: If t3.micro runs for 300 seconds with 90% CPU utilization:
- Base TDP = 6W
- CPU Power = 6W × 0.90 = 5.4W
- Energy = 5.4W × 300s = 1,620 Joules

---

## Part 3: Efficiency Metrics

### Energy Efficiency

**Efficiency = Energy per Work Unit**

```python
efficiency_joules_per_work = energy_joules / work_units_completed
```

**Example**: If t3.micro uses 1,620 Joules and completes 1,000,000 hashes:
- Efficiency = 1,620 J / 1,000,000 hashes = 0.00162 Joules/hash

**Lower is better** - Less energy per unit of work = more efficient

### Normalized Efficiency

**Efficiency per vCPU** = `efficiency / vCPU_count`

Allows fair comparison across instances with different core counts.

### Cost Efficiency

**Cost per Work Unit** = `(instance_hourly_cost × duration_hours) / work_units_completed`

**Example**: If t3.micro ($0.0104/hr) runs for 5 minutes and completes 1,000,000 hashes:
- Duration = 5/60 = 0.0833 hours
- Cost = $0.0104/hr × 0.0833 hr = $0.000867
- Cost per hash = $0.000867 / 1,000,000 = $0.000000000867/hash

---

## Part 4: Complete Measurement Pipeline

### 1. **Workload Execution** (5 minutes)
   - Run workload on EC2 instance
   - Count work units in real-time
   - Output: `total_count`, `measurement_duration_seconds`

### 2. **Monitoring** (Parallel)
   - Collect CloudWatch metrics (CPU%, network, etc.)
   - Collect GPU metrics via SSH (`nvidia-smi`) if applicable
   - Collect memory metrics via SSH if needed
   - Time window: Same as measurement period

### 3. **Energy Estimation** (Post-benchmark)
   - Calculate average CPU utilization from CloudWatch
   - Calculate average GPU power from `nvidia-smi` (if GPU instance)
   - Apply power model: `Power = TDP × (CPU%/100) + GPU_Power`
   - Calculate energy: `Energy = Power × Duration`

### 4. **Normalization** (Post-all-benchmarks)
   - Calculate throughput: `work_units / duration`
   - Calculate efficiency: `energy_joules / work_units`
   - Normalize by vCPU for fair comparison
   - Calculate cost efficiency

### 5. **Aggregation**
   - All results saved to `results/raw_logs/{instance}_{workload}.json`
   - Aggregated into `results/summary.csv` and `results/summary.json`
   - Tables and graphs generated for comparison

---

## Key Design Decisions for Accuracy

### 1. **Comparability**
   - Fixed workload parameters (same difficulty, key sizes, etc.)
   - Fixed measurement window (5 minutes)
   - Warmup period excluded
   - Same software versions

### 2. **Energy Estimation Limitations**
   - **Simplified Model**: Uses linear scaling of TDP by CPU utilization
   - **Real Hardware**: Actual power consumption varies by load type, memory usage, etc.
   - **GPU Power**: Directly measured (more accurate for GPU instances)
   - **Estimated TDP**: Based on AWS published values, may not reflect actual power

### 3. **What's Measured vs. Estimated**

**Measured**:
- ✅ Work units completed (exact count)
- ✅ CPU utilization (% from CloudWatch)
- ✅ GPU power (Watts from nvidia-smi)
- ✅ Time duration (exact)

**Estimated**:
- ⚠️ Base power consumption (TDP values)
- ⚠️ CPU power scaling (linear model)
- ⚠️ Total energy (calculated from estimated power)

---

## Example Results

After running benchmarks, you'll see metrics like:

| Instance | Workload | Throughput | Energy | Efficiency |
|----------|----------|------------|--------|------------|
| t3.micro | pow | 3,333 hash/sec | 1,620 J | 0.00162 J/hash |
| t4g.micro | pow | 3,500 hash/sec | 750 J | 0.00021 J/hash |
| g4dn.xlarge | pow | 50,000 hash/sec | 60,000 J | 0.0012 J/hash |

This allows you to see:
- **Performance**: Which instance completes work faster
- **Energy Efficiency**: Which instance uses less energy per unit of work
- **Trade-offs**: Faster instances may use more energy per work unit

---

## Summary

1. **Performance** = Counted work units per fixed time (work/sec)
2. **Energy** = Estimated from power model (Watts × Time = Joules)
3. **Efficiency** = Energy per work unit (Joules/work) - **lower is better**
4. **Comparability** = Fixed parameters, same measurement window, normalized metrics

This dual measurement approach allows you to identify both the **fastest** and **most energy-efficient** instances for each blockchain consensus workload.

