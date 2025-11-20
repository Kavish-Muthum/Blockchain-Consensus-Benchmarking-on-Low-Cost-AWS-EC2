# Should vCPUs Match Across All Instances?

## The Question

Should all instances have the **same vCPU count** to eliminate it as a confounding variable?

## Short Answer: **Ideally YES, but Practically NO**

### Why Matching vCPUs is Better (In Theory)

✅ **Eliminates confounding variable**
- No need for normalization
- Direct comparison possible
- Cleaner experimental design

✅ **Easier to interpret**
- Results directly comparable
- No statistical adjustments needed
- Clearer conclusions

### Why Matching vCPUs is Hard (In Practice)

❌ **GPU instances don't come small enough**
- Smallest GPU instance: `g4dn.xlarge` = 4 vCPU
- No GPU instance with 2 vCPU exists
- Would need much larger ARM/x86 instances to match

❌ **FPGA instances don't come small enough**
- Smallest FPGA instance: `f1.2xlarge` = 8 vCPU
- No FPGA instance with 2 or 4 vCPU exists
- Would need much larger instances to match

❌ **Cost and feasibility**
- Larger ARM/x86 instances cost much more
- May not be available in all regions
- Defeats purpose of "low-cost" benchmarking

---

## Option 1: Match vCPUs at 2 (Not Possible)

| Hardware | Instance | vCPU | Status |
|----------|----------|------|--------|
| ARM | t4g.small | 2 | ✅ Available |
| x86 | t3.small | 2 | ✅ Available |
| GPU | ??? | 2 | ❌ **Doesn't exist** |
| FPGA | ??? | 2 | ❌ **Doesn't exist** |

**Result**: Not possible - GPU/FPGA instances don't have 2 vCPU options.

---

## Option 2: Match vCPUs at 4 (Possible but Expensive)

| Hardware | Instance | vCPU | RAM | Cost/hr | Status |
|----------|----------|------|-----|---------|--------|
| ARM | t4g.medium | 2 | 4GB | $0.0336 | ❌ Only 2 vCPU |
| ARM | t4g.large | 2 | 8GB | $0.0672 | ❌ Only 2 vCPU |
| ARM | t4g.xlarge | 4 | 16GB | $0.1344 | ✅ Has 4 vCPU |
| x86 | t3.xlarge | 4 | 16GB | $0.1664 | ✅ Has 4 vCPU |
| GPU | g4dn.xlarge | 4 | 16GB | $0.526 | ✅ Has 4 vCPU |
| FPGA | ??? | 4 | ??? | ??? | ❌ **Doesn't exist** |

**Result**: FPGA doesn't have 4 vCPU option. Would need to use larger FPGA instances.

---

## Option 3: Match vCPUs at 8 (Possible but Very Expensive)

| Hardware | Instance | vCPU | RAM | Cost/hr | Status |
|----------|----------|------|-----|---------|--------|
| ARM | t4g.2xlarge | 8 | 32GB | $0.2688 | ✅ Has 8 vCPU |
| x86 | t3.2xlarge | 8 | 32GB | $0.3328 | ✅ Has 8 vCPU |
| GPU | g4dn.2xlarge | 8 | 32GB | $1.204 | ✅ Has 8 vCPU |
| FPGA | f1.2xlarge | 8 | 122GB | $1.65 | ✅ Has 8 vCPU |

**Result**: **Possible, but expensive!**
- ARM/x86 cost: ~$0.30/hr (vs $0.02/hr for small)
- GPU cost: $1.20/hr (vs $0.53/hr for xlarge)
- **15x more expensive** for ARM/x86
- Defeats "low-cost" benchmarking goal

---

## Option 4: Single-Threaded Execution (Best Control)

**Force all workloads to use 1 vCPU:**
- Set CPU affinity to single core
- Disable multiprocessing
- All instances effectively use 1 vCPU

| Hardware | Instance | Actual vCPU | Effective vCPU | Status |
|----------|----------|-------------|----------------|--------|
| ARM | t4g.small | 2 | 1 | ✅ All use 1 |
| x86 | t3.small | 2 | 1 | ✅ All use 1 |
| GPU | g4dn.xlarge | 4 | 1 | ✅ All use 1 |
| FPGA | f1.2xlarge | 8 | 1 | ✅ All use 1 |

**Result**: **Perfect match!** All instances use 1 vCPU.

**Trade-offs:**
- ✅ Eliminates vCPU as variable
- ✅ Cleanest comparison
- ❌ Doesn't show multi-core performance
- ❌ May not reflect real-world usage

---

## Recommendation: **Hybrid Approach**

### Primary: Match ARM/x86, Normalize GPU/FPGA

**Use different strategies for different comparisons:**

1. **ARM vs x86**: Perfect match (identical specs)
   - Direct comparison - no normalization needed
   - Question: "Does ARM or x86 perform better?"

2. **All instances**: Normalize by vCPU
   - Statistical control for vCPU differences
   - Question: "Which hardware is most efficient per core?"

3. **Single-threaded (optional)**: Force all to 1 vCPU
   - Cleanest comparison possible
   - Question: "Which hardware performs best on single core?"

### Current Approach (Recommended)

| Hardware | Instance | vCPU | Strategy |
|----------|----------|------|----------|
| ARM | t4g.small | 2 | Match x86 exactly |
| x86 | t3.small | 2 | Match ARM exactly |
| GPU | g4dn.xlarge | 4 | Normalize by vCPU |
| FPGA | f1.2xlarge | 8 | Normalize by vCPU |

**Analysis:**
- ARM vs x86: **Direct comparison** (identical specs)
- GPU vs FPGA: **Normalized by vCPU** (4 vs 8)
- All instances: **Normalized by vCPU** for overall comparison

---

## Comparison of Approaches

| Approach | ARM/x86 | GPU/FPGA | Cost | Complexity | Recommendation |
|----------|---------|----------|------|------------|----------------|
| **Match at 2 vCPU** | ✅ Same | ❌ Impossible | Low | Simple | ❌ Not possible |
| **Match at 4 vCPU** | ⚠️ Larger instances | ❌ FPGA missing | Medium | Medium | ❌ FPGA unavailable |
| **Match at 8 vCPU** | ⚠️ Much larger | ✅ Same | **High** | Simple | ⚠️ Very expensive |
| **Normalize by vCPU** | ✅ Same | ✅ Normalized | Low | Medium | ✅ **Recommended** |
| **Single-threaded** | ✅ All use 1 | ✅ All use 1 | Low | Medium | ✅ **Best control** |

---

## Final Recommendation

### **Use Current Approach + Single-Threaded Option**

**Primary approach: Normalize by vCPU**
- ARM/x86: Perfect match (identical specs)
- GPU/FPGA: Normalize by vCPU (fair comparison)
- Cost-effective and practical

**Optional: Single-threaded execution**
- Use when you want the cleanest possible comparison
- All instances use 1 vCPU effectively
- Eliminates vCPU as variable entirely

### Implementation

```bash
# Standard approach: Normalize by vCPU
python3 src/benchmarking/runner.py --config config/instances.json

# Single-threaded approach: All use 1 vCPU
python3 src/benchmarking/runner.py --config config/instances_single_thread.json
```

### Analysis Strategy

1. **ARM vs x86**: Direct comparison (identical specs)
2. **GPU vs FPGA**: Normalize by vCPU (4 vs 8)
3. **All instances**: Normalize by vCPU (2 vs 4 vs 8)
4. **Single-threaded (optional)**: All use 1 vCPU

---

## Answer to Your Question

**Should vCPUs match across all instances?**

**Short answer: Ideally yes, but practically no.**

**Better answer:**
- ✅ **Yes for ARM vs x86** (they match at 2 vCPU)
- ⚠️ **No for GPU/FPGA** (they don't have matching sizes)
- ✅ **Normalize by vCPU** for fair comparison
- ✅ **Single-threaded execution** for cleanest comparison

**Current design is optimal:**
- Matches where possible (ARM/x86)
- Normalizes where necessary (GPU/FPGA)
- Provides both normalized and single-threaded options

This gives you the **best possible experimental design** given AWS instance constraints!

