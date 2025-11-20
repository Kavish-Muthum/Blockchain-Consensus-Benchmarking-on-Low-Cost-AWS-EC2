# Benchmark Results Comparison Table
## ARM (t4g.2xlarge) vs x86 (t3.2xlarge) - 8 vCPU Instances

| Workload | Metric | ARM (t4g.2xlarge) | x86 (t3.2xlarge) | Winner |
|----------|--------|-------------------|------------------|---------|
| **POW** | | | | |
| | Throughput (work/sec) | 542,699 | 572,677 | **x86** (+5.5%) |
| | Energy (Joules) | 2,353.7 | 2,524.6 | **ARM** (-6.8%) |
| | Energy Efficiency (J/work) | 1.45×10⁻⁵ | 1.47×10⁻⁵ | **ARM** (1.4% better) |
| | Cost Efficiency (USD/work) | 1.38×10⁻¹⁰ | 1.61×10⁻¹⁰ | **ARM** (14.3% better) |
| | Performance per vCPU | 67,837.3 | 71,584.6 | **x86** (+5.5%) |
| **POS** | | | | |
| | Throughput (work/sec) | 6,081 | 6,549 | **x86** (+7.7%) |
| | Energy (Joules) | 2,160.0 | 2,520.0 | **ARM** (-14.3%) |
| | Energy Efficiency (J/work) | 1.18×10⁻³ | 1.28×10⁻³ | **ARM** (7.8% better) |
| | Cost Efficiency (USD/work) | 1.23×10⁻⁸ | 1.41×10⁻⁸ | **ARM** (12.8% better) |
| | Performance per vCPU | 760.1 | 818.7 | **x86** (+7.7%) |
| **BFT** | | | | |
| | Throughput (work/sec) | 174,816 | 138,137 | **ARM** (+26.5%) |
| | Energy (Joules) | 2,160.0 | 2,520.0 | **ARM** (-14.3%) |
| | Energy Efficiency (J/work) | 4.12×10⁻⁵ | 6.08×10⁻⁵ | **ARM** (32.2% better) |
| | Cost Efficiency (USD/work) | 4.27×10⁻¹⁰ | 6.69×10⁻¹⁰ | **ARM** (36.2% better) |
| | Performance per vCPU | 21,852.0 | 17,267.2 | **ARM** (+26.5%) |
| **ZK** | | | | |
| | Throughput (work/sec) | 5,255 | 6,008 | **x86** (+14.3%) |
| | Energy (Joules) | 2,160.0 | 2,520.0 | **ARM** (-14.3%) |
| | Energy Efficiency (J/work) | 1.37×10⁻³ | 1.40×10⁻³ | **ARM** (2.1% better) |
| | Cost Efficiency (USD/work) | 1.42×10⁻⁸ | 1.54×10⁻⁸ | **ARM** (7.8% better) |
| | Performance per vCPU | 656.9 | 751.0 | **x86** (+14.3%) |

---

## Key Findings

### Performance (Throughput)
- **BFT**: ARM is **26.5% faster** than x86
- **PoW**: x86 is **5.5% faster** than ARM
- **PoS**: x86 is **7.7% faster** than ARM
- **ZK**: x86 is **14.3% faster** than ARM

### Energy Efficiency
- **ARM consistently more energy efficient** across all workloads
- **BFT**: ARM is **32.2% more efficient** than x86
- **PoW**: ARM is **1.4% more efficient** than x86
- **PoS**: ARM is **7.8% more efficient** than x86
- **ZK**: ARM is **2.1% more efficient** than x86

### Cost Efficiency
- **ARM consistently more cost-efficient** across all workloads
- Lower hourly cost ($0.2688 vs $0.3328) combined with better energy efficiency
- **BFT**: ARM is **36.2% more cost-efficient** than x86
- **PoW**: ARM is **14.3% more cost-efficient** than x86
- **PoS**: ARM is **12.8% more cost-efficient** than x86
- **ZK**: ARM is **7.8% more cost-efficient** than x86

### Total Energy Consumption
- ARM consumes **less energy** for all workloads (2,160-2,354 J vs 2,520-2,525 J)
- ARM: **2,160-2,353 Joules** (300 seconds)
- x86: **2,520-2,525 Joules** (300 seconds)
- ARM advantage: **6.8-14.3% lower energy consumption**

---

## Summary

**ARM (t4g.2xlarge)** excels at:
- ✅ Energy efficiency (all workloads)
- ✅ Cost efficiency (all workloads)
- ✅ BFT workload performance (26.5% faster)
- ✅ Lower total energy consumption

**x86 (t3.2xlarge)** excels at:
- ✅ PoW, PoS, and ZK throughput (slightly faster)
- ✅ Raw performance for crypto workloads (PoW, PoS, ZK)

**Overall**: ARM provides better energy and cost efficiency across all workloads, making it the better choice for energy-conscious deployments, while x86 offers slightly better raw performance for certain cryptographic workloads.

---

## Energy Calculation Note

Energy values are **estimated** using:
- **Idle Power**: 30% of TDP (instances consume power even at 0% CPU)
- **Active Power**: 70% of TDP × CPU utilization
- **TDP**: 24W (ARM), 28W (x86)
- **Formula**: `Energy (Joules) = (Idle Power + Active Power) × Duration (seconds)`

See `ENERGY_CALCULATION_EXPLANATION.md` for detailed explanation.

