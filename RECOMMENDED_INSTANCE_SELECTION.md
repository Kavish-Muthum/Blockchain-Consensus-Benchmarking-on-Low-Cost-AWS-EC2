# Recommended Instance Selection: Minimizing Extraneous Variables

## The Problem

Current selection has **too many differences**:
- vCPU: 2 vs 4 vs 8 (3x difference!)
- RAM: 1GB vs 16GB vs 122GB (122x difference!)
- Instance families: burstable vs fixed
- Makes it impossible to isolate hardware type effect

## Best Solution: **t4g.small + t3.small** (ARM/x86 Match Perfectly)

### Recommended Instance Set

| Hardware | Instance | vCPU | RAM | Network | Family | Price/hr |
|----------|----------|------|-----|---------|--------|----------|
| **ARM** | **t4g.small** | **2** | **2GB** | 5 Gbps | Burstable | $0.0168 |
| **x86** | **t3.small** | **2** | **2GB** | 5 Gbps | Burstable | $0.0208 |
| **GPU** | **g4dn.xlarge** | 4 | 16GB | 25 Gbps | Fixed | $0.526 |
| **FPGA** | **f1.2xlarge** | 8 | 122GB | 10 Gbps | Fixed | $1.65 |

### Key Improvements

✅ **ARM vs x86: IDENTICAL specs**
- Same vCPU (2)
- Same RAM (2GB)
- Same network (5 Gbps)
- Same family (burstable)
- **Only difference: Architecture (ARM vs x86)**

⚠️ **GPU/FPGA: Still different, but normalized**
- Different vCPU (4 vs 8)
- Different RAM (16GB vs 122GB)
- **Solution: Normalize by vCPU in analysis**

---

## Experimental Design Modifications

### 1. Use Better-Matched Instances

**Update `config/instances.json` to use:**
- `t4g.small` instead of `t4g.micro` (ARM)
- `t3.small` instead of `t3.micro` (x86)
- Keep `g4dn.xlarge` and `f1.2xlarge` (smallest available)

### 2. Statistical Normalization

**Normalize all metrics by vCPU:**
- `throughput_per_vcpu` = throughput / vCPU
- `efficiency_per_vcpu` = efficiency / vCPU
- `energy_per_vcpu` = energy / vCPU

**Result**: Compare "performance per core" across all instances.

### 3. Single-Threaded Workloads (Optional - Cleanest)

**Force all workloads to use 1 CPU core:**
- Set CPU affinity to single core
- Disable multiprocessing
- All instances effectively use 1 vCPU

**Result**: Eliminates vCPU as confounding variable entirely.

### 4. Control RAM Usage

**Limit all workloads to <1GB RAM:**
- Ensures RAM differences don't affect results
- All instances have sufficient RAM
- Workloads run in-memory, not disk

---

## Comparison: Current vs Recommended

### Current Selection (Too Many Differences)

```
ARM:   t4g.micro  → 2 vCPU, 1GB RAM
x86:   t3.micro   → 2 vCPU, 1GB RAM  ✅ Match
GPU:   g4dn.xlarge → 4 vCPU, 16GB RAM  ❌ 2x vCPU, 16x RAM
FPGA:  f1.2xlarge  → 8 vCPU, 122GB RAM ❌ 4x vCPU, 122x RAM
```

**Problems:**
- GPU has 2x more vCPU than ARM/x86
- FPGA has 4x more vCPU than ARM/x86
- RAM differences are massive

### Recommended Selection (Minimal Differences)

```
ARM:   t4g.small  → 2 vCPU, 2GB RAM
x86:   t3.small   → 2 vCPU, 2GB RAM  ✅ Perfect match!
GPU:   g4dn.xlarge → 4 vCPU, 16GB RAM  ⚠️ 2x vCPU (normalize)
FPGA:  f1.2xlarge  → 8 vCPU, 122GB RAM ⚠️ 4x vCPU (normalize)
```

**Improvements:**
- ✅ ARM and x86: **Perfect match** (identical specs)
- ⚠️ GPU/FPGA: Still different, but normalize by vCPU
- ✅ RAM: Workloads use <1GB, so differences don't matter

---

## Analysis Strategy

### Primary Comparison: ARM vs x86
- **Direct comparison**: No normalization needed
- **Question**: "Does ARM or x86 perform better?"
- **Answer**: Direct from results (identical specs)

### Secondary Comparison: All Hardware Types
- **Normalized by vCPU**: All metrics per vCPU
- **Question**: "Which hardware is most efficient per core?"
- **Answer**: From normalized metrics

### Tertiary Comparison: GPU vs FPGA
- **Normalized by vCPU**: Both normalized
- **Question**: "Which accelerator is more efficient per core?"
- **Answer**: From normalized metrics

---

## Implementation

### Option A: Use Better-Matched Instances (Recommended)

```bash
# Use minimal differences config
python3 src/benchmarking/runner.py \
    --config config/instances_minimal_diff.json
```

**Benefits:**
- ARM/x86 perfect match
- GPU/FPGA normalized by vCPU
- Minimal confounding variables

### Option B: Single-Threaded Execution (Cleanest)

```bash
# Use single-threaded config
python3 src/benchmarking/runner.py \
    --config config/instances_single_thread.json
```

**Benefits:**
- All instances use 1 vCPU effectively
- Eliminates vCPU as variable
- Cleanest comparison possible

**Trade-off:**
- Doesn't show multi-core performance
- May not reflect real-world usage

---

## Recommended Approach

### **Use t4g.small + t3.small + Normalization**

1. **Update instances.json** to use `t4g.small` and `t3.small`
2. **Normalize all metrics by vCPU** (already implemented)
3. **Document differences** in results
4. **Run both**:
   - Baseline: Same algorithm (fair comparison)
   - Optimized: Hardware-specific (best performance)

This gives you:
- ✅ Perfect ARM vs x86 comparison (identical specs)
- ✅ Controlled GPU/FPGA comparison (normalized)
- ✅ Overall comparison (all normalized)
- ✅ Clear documentation of limitations

---

## Summary

**Best Instance Selection:**
- **t4g.small** (ARM) - 2 vCPU, 2GB RAM
- **t3.small** (x86) - 2 vCPU, 2GB RAM ← **Perfect match!**
- **g4dn.xlarge** (GPU) - 4 vCPU, 16GB RAM ← Normalize by vCPU
- **f1.2xlarge** (FPGA) - 8 vCPU, 122GB RAM ← Normalize by vCPU

**Key Benefit:**
- ARM and x86 have **identical specs** - perfect direct comparison
- GPU and FPGA normalized by vCPU for fair comparison
- Minimal extraneous variables

This is the **best possible** given AWS instance constraints!

