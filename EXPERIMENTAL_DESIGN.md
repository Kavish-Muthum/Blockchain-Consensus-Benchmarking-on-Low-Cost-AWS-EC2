# Experimental Design: Minimizing Extraneous Variables

## Problem with Current Instance Selection

Current instances have **many differences** beyond just hardware type:

| Instance | Hardware | vCPU | RAM | Network | Burstable | Price/hr |
|----------|----------|------|-----|---------|-----------|----------|
| t4g.micro | ARM | 2 | 1GB | 5 Gbps | Yes | $0.0084 |
| t3.micro | x86 | 2 | 1GB | 5 Gbps | Yes | $0.0104 |
| g4dn.xlarge | GPU | 4 | 16GB | 25 Gbps | No | $0.526 |
| f1.2xlarge | FPGA | 8 | 122GB | 10 Gbps | No | $1.65 |

**Confounding Variables:**
- ❌ Different vCPU counts (2 vs 4 vs 8)
- ❌ Different RAM (1GB vs 16GB vs 122GB)
- ❌ Different network performance
- ❌ Different instance families (burstable vs fixed)
- ❌ Different pricing tiers

This makes it **impossible to isolate** the effect of hardware type (ARM vs x86 vs GPU vs FPGA).

---

## Solution: Better Instance Selection

### Option 1: Similar Spec Instances (Recommended)

Find instances with **matching vCPU and RAM** where possible:

| Hardware | Instance | vCPU | RAM | Notes |
|----------|----------|------|-----|-------|
| **ARM** | t4g.small | 2 | 2GB | Closest to others |
| **x86** | t3.small | 2 | 2GB | Matches ARM |
| **GPU** | g4dn.2xlarge | 8 | 32GB | More vCPU, but needed for GPU |
| **FPGA** | f1.2xlarge | 8 | 122GB | Matches GPU vCPU |

**Still has differences, but better:**
- ✅ ARM and x86: Same vCPU (2) and RAM (2GB)
- ✅ GPU and FPGA: Same vCPU (8)
- ⚠️ RAM still differs (2GB vs 32GB vs 122GB)
- ⚠️ GPU/FPGA have more vCPU than ARM/x86

### Option 2: Normalize by vCPU (Statistical Control)

Keep current instances but **normalize all metrics by vCPU**:

- Throughput per vCPU
- Energy per vCPU
- Cost per vCPU

This controls for vCPU differences statistically.

### Option 3: Match Instance Families (Best Control)

Use instances from **same family** where possible:

| Hardware | Instance | vCPU | RAM | Family |
|----------|----------|------|-----|--------|
| **ARM** | t4g.medium | 2 | 4GB | t4g (burstable) |
| **x86** | t3.medium | 2 | 4GB | t3 (burstable) |
| **GPU** | g4dn.medium | 1 | 4GB | g4dn (fixed) |
| **FPGA** | f1.medium | ? | ? | f1 (fixed) |

**Problem**: GPU and FPGA don't have small instances with matching specs.

---

## Recommended Approach: **Normalized Comparison**

### Strategy: Control Variables Statistically

Since we can't get identical specs across all hardware types, use:

1. **Normalize by vCPU**: All metrics per vCPU
2. **Normalize by RAM**: Memory-intensive workloads per GB
3. **Document differences**: Clearly state what differs
4. **Statistical analysis**: Account for differences in analysis

### Modified Instance Selection

**Option A: Minimal Differences (Recommended)**

| Hardware | Instance | vCPU | RAM | Why Selected |
|----------|----------|------|-----|--------------|
| **ARM** | **t4g.small** | 2 | 2GB | Smallest ARM with reasonable RAM |
| **x86** | **t3.small** | 2 | 2GB | Matches ARM exactly |
| **GPU** | **g4dn.xlarge** | 4 | 16GB | Smallest GPU instance (NVIDIA T4) |
| **FPGA** | **f1.2xlarge** | 8 | 122GB | Smallest FPGA instance |

**Differences:**
- vCPU: 2 (ARM/x86) vs 4 (GPU) vs 8 (FPGA)
- RAM: 2GB (ARM/x86) vs 16GB (GPU) vs 122GB (FPGA)

**Control Strategy:**
- Normalize throughput by vCPU
- Normalize energy by vCPU
- Note RAM differences in analysis

**Option B: Match vCPU (Better Control)**

| Hardware | Instance | vCPU | RAM | Why Selected |
|----------|----------|------|-----|--------------|
| **ARM** | **t4g.medium** | 2 | 4GB | Standard ARM |
| **x86** | **t3.medium** | 2 | 4GB | Matches ARM |
| **GPU** | **g4dn.2xlarge** | 8 | 32GB | Match FPGA vCPU |
| **FPGA** | **f1.2xlarge** | 8 | 122GB | Match GPU vCPU |

**Differences:**
- ✅ GPU and FPGA: Same vCPU (8)
- ✅ ARM and x86: Same vCPU (2)
- ⚠️ RAM: 4GB vs 32GB vs 122GB

---

## Experimental Design Modifications

### 1. Statistical Normalization

**Normalize all metrics by vCPU:**
```python
throughput_per_vcpu = throughput / vcpu_count
energy_per_vcpu = energy_joules / vcpu_count
efficiency_per_vcpu = efficiency / vcpu_count
```

**Result**: Compare "performance per core" rather than absolute performance.

### 2. Fixed Workload Size

**Use workload sizes that fit in smallest RAM:**
- All workloads use ≤ 1GB RAM
- Ensures RAM differences don't affect results
- Workloads run in memory, not disk

### 3. Document Confounding Variables

**In results, clearly state:**
- Instance specs (vCPU, RAM) for each
- What was normalized and how
- Limitations of comparison

### 4. Sensitivity Analysis

**Run additional tests:**
- Test ARM/x86 with same vCPU (already matched)
- Test GPU with different vCPU counts (if possible)
- Analyze if vCPU normalization is sufficient

---

## Proposed Instance Configuration

### Recommended: Minimal Differences

```json
{
  "t4g.small": {
    "architecture": "arm64",
    "category": "ARM",
    "vCPU": 2,
    "memory_gb": 2,
    "hourly_cost_usd": 0.0168
  },
  "t3.small": {
    "architecture": "x86_64",
    "category": "x86",
    "vCPU": 2,
    "memory_gb": 2,
    "hourly_cost_usd": 0.0208
  },
  "g4dn.xlarge": {
    "architecture": "x86_64",
    "category": "GPU",
    "vCPU": 4,
    "memory_gb": 16,
    "hourly_cost_usd": 0.526
  },
  "f1.2xlarge": {
    "architecture": "x86_64",
    "category": "FPGA",
    "vCPU": 8,
    "memory_gb": 122,
    "hourly_cost_usd": 1.65
  }
}
```

**Key Improvements:**
- ✅ ARM and x86: **Identical specs** (2 vCPU, 2GB RAM)
- ⚠️ GPU: 4 vCPU (smallest available)
- ⚠️ FPGA: 8 vCPU (smallest available)
- ✅ Normalize GPU/FPGA by vCPU for comparison

---

## Analysis Strategy

### Primary Comparison: ARM vs x86
- **Direct comparison**: Same vCPU, RAM, family
- **No normalization needed**: Identical specs
- **Question**: "Does ARM or x86 perform better for blockchain workloads?"

### Secondary Comparison: GPU vs FPGA
- **Normalized comparison**: Both normalized by vCPU
- **Question**: "Which is more efficient per core?"

### Tertiary Comparison: All Hardware Types
- **Normalized by vCPU**: All metrics per vCPU
- **Question**: "Which hardware type is most efficient per core?"

---

## Alternative: Single-Threaded Workloads

### Force Single-Threaded Execution

**Modify workloads to use only 1 CPU core:**
- Set CPU affinity to single core
- Disable multiprocessing
- Use single-threaded algorithms

**Result:**
- All instances effectively use 1 vCPU
- Eliminates vCPU as confounding variable
- Fair comparison of hardware types

**Trade-off:**
- Doesn't show multi-core performance
- May not reflect real-world usage
- But provides cleanest comparison

---

## Recommendation

### Best Approach: **Hybrid Strategy**

1. **Use t4g.small and t3.small** (ARM/x86 with identical specs)
2. **Keep g4dn.xlarge and f1.2xlarge** (smallest GPU/FPGA)
3. **Normalize all metrics by vCPU**
4. **Run single-threaded workloads** (optional, for cleanest comparison)
5. **Document all differences** in results

### Implementation

- Update `config/instances.json` with better-matched instances
- Add normalization flags to analysis
- Document experimental design in report
- Provide both normalized and raw metrics

This gives you:
- ✅ Clean ARM vs x86 comparison (identical specs)
- ✅ Controlled GPU vs FPGA comparison (normalized)
- ✅ Overall comparison (all normalized by vCPU)
- ✅ Clear documentation of limitations

