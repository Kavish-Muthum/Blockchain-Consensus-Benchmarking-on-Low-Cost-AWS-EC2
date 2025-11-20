# Comprehensive Benchmark Results Summary

## ARM vs x86 Performance Comparison (8 vCPU Instances)

### 1. Performance (Throughput)

| Workload | ARM (t4g.2xlarge) | x86 (t3.2xlarge) | Winner | Difference |
|----------|-------------------|------------------|--------|------------|
| **POW** | 542,698.65 work/s | 572,676.53 work/s | x86 | +5.5% |
| **POS** | 6,080.51 work/s | 6,549.27 work/s | x86 | +7.7% |
| **BFT** | 174,815.97 work/s | 138,137.31 work/s | ARM | +26.6% |
| **ZK** | 5,255.34 work/s | 6,007.87 work/s | x86 | +14.3% |

### 2. Energy Efficiency (Joules per Work Unit)

| Workload | ARM (t4g.2xlarge) | x86 (t3.2xlarge) | Winner | Improvement |
|----------|-------------------|------------------|--------|-------------|
| **POW** | 1.45e-05 J/work | 1.47e-05 J/work | ARM | 1.6% better |
| **POS** | 1.18e-03 J/work | 1.28e-03 J/work | ARM | 7.7% better |
| **BFT** | 4.12e-05 J/work | 6.08e-05 J/work | ARM | 32.3% better |
| **ZK** | 1.37e-03 J/work | 1.40e-03 J/work | ARM | 2.0% better |

### 3. Cost Efficiency (USD per Work Unit)

| Workload | ARM (t4g.2xlarge) | x86 (t3.2xlarge) | Winner | Savings |
|----------|-------------------|------------------|--------|----------|
| **POW** | $1.38e-10 | $1.61e-10 | ARM | 14.8% cheaper |
| **POS** | $1.23e-08 | $1.41e-08 | ARM | 13.0% cheaper |
| **BFT** | $4.27e-10 | $6.69e-10 | ARM | 36.2% cheaper |
| **ZK** | $1.42e-08 | $1.54e-08 | ARM | 7.7% cheaper |

### 4. Total Energy Consumption

| Workload | ARM (t4g.2xlarge) | x86 (t3.2xlarge) | Difference |
|----------|-------------------|------------------|------------|
| **POW** | 2353.72 J | 2524.60 J | 170.88 J (+6.8%) |
| **POS** | 2160.00 J | 2520.00 J | 360.00 J (+14.3%) |
| **BFT** | 2160.00 J | 2520.00 J | 360.00 J (+14.3%) |
| **ZK** | 2160.00 J | 2520.00 J | 360.00 J (+14.3%) |

### 5. Summary Statistics

| Metric | ARM (t4g.2xlarge) | x86 (t3.2xlarge) |
|--------|-------------------|------------------|
| **Average Throughput** | 182,212.62 work/s | 180,842.74 work/s |
| **Average Energy Efficiency** | 6.52e-04 J/work | 6.89e-04 J/work |
| **Average Cost Efficiency** | $6.76e-09 | $7.58e-09 |
| **Average Energy Consumption** | 2208.43 J | 2521.15 J |
