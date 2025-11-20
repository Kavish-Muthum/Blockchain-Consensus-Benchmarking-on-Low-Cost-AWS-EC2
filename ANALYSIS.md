# Benchmark Results Analysis

## Overview

This document provides a comprehensive analysis of the blockchain consensus workload benchmarks comparing ARM (t4g.2xlarge) and x86 (t3.2xlarge) instances with 8 vCPU each.

## Key Findings

### 1. Proof of Work (PoW) - SHA-256 Mining

**Performance Comparison**:
- **ARM (t4g.2xlarge)**: 542,698.65 hashes/sec
- **x86 (t3.2xlarge)**: 572,676.53 hashes/sec
- **Winner**: x86 is **5.5% faster** than ARM

**Per-Core Performance** (8 vCPU):
- ARM: 67,837.33 hashes/sec/core
- x86: 71,584.57 hashes/sec/core
- **x86 is 5.5% faster per core**

**Energy Efficiency** (only ARM has energy data):
- ARM: 1.70 × 10⁻⁶ Joules/hash (276.74 Joules total)
- x86: Energy data not available (0.0 Joules)

**Analysis**:
- x86 shows slight performance advantage for SHA-256 hashing
- This could be due to x86-optimized OpenSSL implementations
- ARM shows good performance, only 5.5% slower
- Both architectures efficiently utilize all 8 CPU cores

**Cost Efficiency**:
- ARM: $1.38 × 10⁻¹⁰ USD/hash
- x86: $1.61 × 10⁻¹⁰ USD/hash
- **ARM is 14.3% cheaper** (lower hourly cost: $0.2688 vs $0.3328)

---

### 2. Proof of Stake (PoS) - Ed25519 Signature Verification

**Performance Comparison**:
- **ARM (t4g.2xlarge)**: 6,080.51 signatures/sec
- **x86 (t3.2xlarge)**: 6,549.27 signatures/sec
- **Winner**: x86 is **7.7% faster** than ARM

**Per-Core Performance** (8 vCPU):
- ARM: 760.06 signatures/sec/core
- x86: 818.66 signatures/sec/core
- **x86 is 7.7% faster per core**

**Energy Efficiency**: Not available (0.0 Joules for both)

**Analysis**:
- x86 maintains performance advantage for cryptographic operations
- Ed25519 signature verification benefits from x86 instruction set optimizations
- Performance difference is modest (~8%), showing both architectures are capable

**Cost Efficiency**:
- ARM: $1.23 × 10⁻⁸ USD/signature
- x86: $1.41 × 10⁻⁸ USD/signature
- **ARM is 12.8% cheaper**

---

### 3. Byzantine Fault Tolerance (BFT) - PBFT Consensus

**Performance Comparison**:
- **ARM (t4g.2xlarge)**: 174,815.97 rounds/sec
- **x86 (t3.2xlarge)**: 138,137.31 rounds/sec
- **Winner**: ARM is **26.5% faster** than x86

**Per-Core Performance** (8 vCPU):
- ARM: 21,852.00 rounds/sec/core
- x86: 17,267.16 rounds/sec/core
- **ARM is 26.5% faster per core**

**Energy Efficiency**: Not available (0.0 Joules for both)

**Analysis**:
- **ARM significantly outperforms x86** for BFT consensus simulation
- This is the only workload where ARM is faster
- The workload involves:
  - Python object manipulation (consensus state)
  - Message hashing (SHA-256)
  - State machine logic (pure Python)
- ARM's advantage likely comes from:
  - Better memory access patterns
  - More efficient Python interpreter performance
  - Cache efficiency for object-heavy workloads

**Cost Efficiency**:
- ARM: $4.27 × 10⁻¹⁰ USD/round
- x86: $6.69 × 10⁻¹⁰ USD/round
- **ARM is 36.2% cheaper** (and faster!)

---

### 4. Zero-Knowledge Proofs (ZK) - ZK-SNARK Simulation

**Performance Comparison**:
- **ARM (t4g.2xlarge)**: 5,255.34 proofs/sec
- **x86 (t3.2xlarge)**: 6,007.87 proofs/sec
- **Winner**: x86 is **14.3% faster** than ARM

**Per-Core Performance** (8 vCPU):
- ARM: 656.92 proofs/sec/core
- x86: 750.98 proofs/sec/core
- **x86 is 14.3% faster per core**

**Energy Efficiency**: Not available (0.0 Joules for both)

**Analysis**:
- x86 shows stronger performance for ZK proof simulation
- The workload involves many hash operations (simulating constraint evaluation)
- x86's hash computation advantage (similar to PoW) applies here

**Cost Efficiency**:
- ARM: $1.42 × 10⁻⁸ USD/proof
- x86: $1.54 × 10⁻⁸ USD/proof
- **ARM is 7.8% cheaper**

---

## Summary: ARM vs x86 Performance

| Workload | ARM (t4g.2xlarge) | x86 (t3.2xlarge) | Winner | Difference |
|----------|-------------------|------------------|--------|------------|
| **PoW** | 542,699 hashes/s | 572,677 hashes/s | x86 | +5.5% |
| **PoS** | 6,081 sigs/s | 6,549 sigs/s | x86 | +7.7% |
| **BFT** | 174,816 rounds/s | 138,137 rounds/s | **ARM** | **+26.5%** |
| **ZK** | 5,255 proofs/s | 6,008 proofs/s | x86 | +14.3% |

**Overall**: x86 wins 3/4 workloads, but ARM wins BFT by a significant margin.

---

## Key Insights

### 1. Workload-Specific Performance

**x86 Advantages**:
- Hash computation (PoW, ZK): Better OpenSSL optimizations
- Cryptographic operations (PoS): Better instruction set support

**ARM Advantages**:
- Python-heavy workloads (BFT): Better interpreter and memory performance
- Object manipulation: Better cache efficiency

### 2. Cost Efficiency

**ARM is consistently cheaper** (~12-36% lower cost per work unit):
- Lower hourly cost: $0.2688 vs $0.3328 (24% cheaper)
- Even when slower, ARM often wins on cost-per-work due to lower pricing

### 3. Performance per Dollar

| Workload | ARM (work/$/hr) | x86 (work/$/hr) | Winner |
|----------|-----------------|-----------------|--------|
| PoW | 2.02M hashes/$ | 1.72M hashes/$ | **ARM** |
| PoS | 22.6K sigs/$ | 19.7K sigs/$ | **ARM** |
| BFT | 650K rounds/$ | 415K rounds/$ | **ARM** |
| ZK | 19.6K proofs/$ | 18.0K proofs/$ | **ARM** |

**ARM wins on all workloads** when considering cost efficiency!

---

## Recommendations

### For Maximum Performance
- **Use x86** for hash-intensive workloads (PoW, ZK)
- **Use x86** for cryptographic operations (PoS)
- **Use ARM** for Python-heavy, state-machine workloads (BFT)

### For Maximum Cost Efficiency
- **Use ARM** for all workloads
- ARM provides 12-36% better cost efficiency
- ARM's lower hourly cost offsets performance differences

### For Balanced Approach
- **Use ARM** if performance difference is <15% (most workloads)
- **Use x86** if maximum performance is critical (PoW, PoS, ZK)
- **Always use ARM** for BFT consensus

---

## Limitations and Notes

### Energy Efficiency Data
- Energy measurements show 0.0 Joules for most benchmarks
- This is likely due to CloudWatch metric collection timing or TDP estimation issues
- Only PoW on ARM has valid energy data (276.74 Joules)

### Missing Benchmarks
- t3.micro and t4g.micro show 0 work units (likely failed or incomplete)
- pow_gpu shows 0 work units (GPU workload not properly executed)

### Data Quality
- All successful benchmarks are from t3.2xlarge and t4g.2xlarge (8 vCPU instances)
- Comparison is fair: identical specs (8 vCPU, 32GB RAM)
- Results are directly comparable

---

## Conclusion

The benchmarks reveal that:

1. **x86 generally outperforms ARM** for CPU-intensive, hash-based workloads
2. **ARM outperforms x86** for Python-heavy, state-machine workloads (BFT)
3. **ARM is consistently more cost-efficient** for all workloads
4. **Performance differences are modest** (5-26%), making cost often the deciding factor

**Recommendation**: Use **ARM instances** for blockchain consensus workloads due to superior cost efficiency, unless maximum performance is required for specific hash-intensive operations.

