# Blockchain Consensus Benchmarking on Low-Cost AWS EC2

This project benchmarks major blockchain consensus workloads on the lowest-cost AWS EC2 instances from each hardware category, measuring performance and resource/energy efficiency.

## Overview

The benchmark tests four consensus algorithms across four EC2 instance types:
- **Proof of Work (PoW)**: SHA-256 mining
- **Proof of Stake (PoS)**: Ed25519 signature verification
- **Byzantine Fault Tolerance (BFT)**: PBFT consensus simulation
- **Zero-Knowledge Proofs (ZK)**: ZK-SNARK proof generation

### Instance Types Tested

| Instance Type | Architecture | Category | vCPU | Memory | Estimated TDP | Hourly Cost (us-east-1) | Notes |
|--------------|-------------|----------|------|--------|---------------|-------------------------|-------|
| t4g.small    | ARM (arm64) | ARM      | 2    | 2 GB   | 6W            | $0.0168                | Matches t3.small exactly |
| t3.small     | x86_64      | x86      | 2    | 2 GB   | 7W            | $0.0208                | Matches t4g.small exactly |
| g4dn.xlarge  | x86_64      | GPU      | 4    | 16 GB  | 200W          | $0.526                 | Normalize by vCPU for comparison |
| f1.2xlarge   | x86_64      | FPGA     | 8    | 122 GB | 150W          | $1.65                  | Normalize by vCPU for comparison |

**Note**: ARM and x86 instances have **identical specs** (2 vCPU, 2GB RAM) for perfect direct comparison. GPU and FPGA instances are normalized by vCPU in analysis. See `RECOMMENDED_INSTANCE_SELECTION.md` for experimental design details.

## Project Structure

```
.
├── config/
│   ├── instances.json    # EC2 instance configurations
│   └── workloads.json    # Workload parameters
├── src/
│   ├── workloads/        # Consensus workload implementations
│   ├── benchmarking/     # EC2 provisioning, monitoring, runner
│   └── visualization/    # Table and graph generation
├── scripts/
│   ├── setup.sh         # Environment setup
│   └── run_benchmarks.sh # Main execution script
├── results/
│   ├── raw_logs/        # Raw benchmark output
│   ├── tables/          # Generated comparison tables
│   ├── graphs/          # Generated visualizations
│   ├── summary.json     # Aggregated results (JSON)
│   └── summary.csv      # Aggregated results (CSV)
└── requirements.txt     # Python dependencies
```

## Setup Instructions

### Prerequisites

- Python 3.8+
- AWS account with EC2 and CloudWatch access
- AWS credentials configured (via `~/.aws/credentials` or IAM role)
- IAM permissions for:
  - EC2: Launch, describe, terminate instances
  - CloudWatch: Read metrics
  - IAM: Read roles (if using IAM roles)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd EnergyEfficientComputingResearch
```

2. Run setup script:
```bash
./scripts/setup.sh
```

3. Configure AWS credentials (if not using IAM role):
```bash
aws configure
```

## Usage

### Benchmarking Strategies

The framework supports two benchmarking approaches:

#### 1. Baseline Benchmarks (Same Algorithm)
Fair hardware comparison using identical workloads:
```bash
./scripts/run_baseline_only.sh
```
- Runs CPU-only versions on ALL instances
- Fair comparison of hardware performance
- Shows: "How does each instance perform on the same workload?"

#### 2. Optimized Benchmarks (Hardware-Specific)
Best-case performance with hardware-specific optimization:
```bash
./scripts/run_optimized_only.sh
```
- GPU instances: GPU-accelerated workloads (`pow_gpu`)
- FPGA instances: FPGA-accelerated workloads (`zk_cloudzk`)
- CPU instances: Standard workloads (already CPU-optimized)
- Shows: "What's the maximum performance achievable on each hardware?"

#### 3. Default (Hybrid - Recommended)
Automatically uses optimized versions when available:
```bash
# Using IAM role (recommended)
export IAM_ROLE='your-iam-role-name'
./scripts/run_benchmarks.sh

# Using default AWS credentials
./scripts/run_benchmarks.sh
```
- Automatically selects GPU/FPGA versions on appropriate instances
- Falls back to CPU versions if optimized unavailable
- Provides both baseline and optimized results

See `BENCHMARKING_STRATEGY.md` for detailed comparison of approaches.

The script will:
1. Provision EC2 instances for each instance type
2. Run all workloads on each instance
3. Collect CloudWatch metrics and custom metrics (GPU/FPGA)
4. Normalize and aggregate results
5. Generate comparison tables and visualizations
6. Clean up all instances

### Running Individual Benchmarks

To run a specific benchmark:

```bash
python3 src/benchmarking/runner.py \
    --instance t3.micro \
    --workload pow \
    --iam-role your-iam-role-name
```

### Monitoring Progress

To monitor benchmark progress in real-time from another terminal:

```bash
# In a new terminal window
./scripts/monitor_progress.sh
```

Or use `tail` directly:

```bash
tail -f results/benchmark_progress.log
```

The progress log includes:
- Benchmark counters (e.g., `[1/16]` for benchmark 1 of 16)
- Instance provisioning status
- Workload deployment progress
- Real-time work unit progress (work units/sec) during measurement periods
- Completion summaries with throughput and energy metrics

The log file is automatically created at `results/benchmark_progress.log` when benchmarks start.

### Cleanup

To manually terminate all benchmark instances:

```bash
python3 src/benchmarking/cleanup.py
```

## Results

### Generated Files

After running benchmarks, results are available in the `results/` directory:

- **`summary.csv`**: Aggregated results in CSV format
- **`summary.json`**: Aggregated results in JSON format
- **`benchmark_progress.log`**: Real-time progress log (view with `tail -f` or `./scripts/monitor_progress.sh`)
- **`raw_logs/`**: Raw benchmark output per instance/workload combination
- **`tables/`**: Markdown tables comparing results
- **`graphs/`**: Visualization graphs (PNG format)
- **`benchmark_report.pdf`**: Comprehensive PDF report with analysis

### Tables

Generated tables in `results/tables/`:
- `summary.md`: Overview table comparing all instance types and workloads
- `workload_pow.md`: PoW-specific results
- `workload_pos.md`: PoS-specific results
- `workload_bft.md`: BFT-specific results
- `workload_zk.md`: ZK-specific results

### Graphs

Generated visualizations in `results/graphs/`:

#### Performance Plots (one per workload)
- `performance_pow.png`: Throughput (hashes/sec) by instance type
- `performance_pos.png`: Throughput (signatures/sec) by instance type
- `performance_bft.png`: Throughput (rounds/sec) by instance type
- `performance_zk.png`: Throughput (proofs/sec) by instance type

#### Efficiency Plots (one per workload)
- `efficiency_pow.png`: Energy per work unit (Joules/hash) by instance type
- `efficiency_pos.png`: Energy per work unit (Joules/signature) by instance type
- `efficiency_bft.png`: Energy per work unit (Joules/round) by instance type
- `efficiency_zk.png`: Energy per work unit (Joules/proof) by instance type

#### Cost Efficiency Plots (one per workload)
- `cost_pow.png`: Cost per work unit (USD/hash) by instance type
- `cost_pos.png`: Cost per work unit (USD/signature) by instance type
- `cost_bft.png`: Cost per work unit (USD/round) by instance type
- `cost_zk.png`: Cost per work unit (USD/proof) by instance type

#### Resource Utilization Plots
- `utilization_{workload}_{instance_type}.png`: CPU and memory utilization for each workload/instance combination

#### Comparison Heatmap
- `comparison_heatmap.png`: Heatmap showing throughput across all workloads and instance types

#### PDF Report
- `benchmark_report.pdf`: Comprehensive PDF report including:
  - Executive summary with key findings
  - Detailed test methodology explanation
  - Performance and energy efficiency analysis
  - Verbose logs from all benchmark runs
  - Visualizations (graphs embedded)
  - Conclusions and recommendations

## Comparability Strategy

To ensure fair comparison across instance types:

1. **Fixed Workload Parameters**: Same difficulty targets, key sizes, node counts, and circuit definitions across all instances
2. **Timing Standardization**: Exact 5-minute measurement window with 30-second warmup period
3. **Environment Consistency**: Same AMI families, dependency versions, and monitoring resolution
4. **Normalization Metrics**: Throughput per vCPU accounts for different core counts; energy calculated using AWS TDP values
5. **Measurement Boundaries**: Only work units completed during the measurement window are counted

## Workload Details

### Proof of Work (PoW)
- Algorithm: SHA-256 hashing
- Fixed difficulty target: Leading zeros requirement
- Work unit: Hash attempts
- Single-threaded for consistency

### Proof of Stake (PoS)
- Algorithm: Ed25519 signature verification
- Pre-generated test message/signature pairs for consistency
- Work unit: Signature verifications
- Same key sizes and cryptographic parameters

### Byzantine Fault Tolerance (BFT)
- Algorithm: PBFT consensus simulation
- Fixed configuration: 4 nodes, 1 Byzantine tolerance
- Work unit: Consensus rounds completed
- Same message sizes and consensus logic

### Zero-Knowledge Proofs (ZK)
- **zk**: Simplified ZK-SNARK simulation (CPU-only)
- **zk_cloudzk**: Cloud-ZK FPGA-accelerated version using BLS12-377 MSM acceleration
- Work unit: Proofs generated
- **Cloud-ZK Integration**: Uses open-source Cloud-ZK toolkit for FPGA acceleration on F1 instances
- See `CLOUD_ZK_INTEGRATION.md` for Cloud-ZK setup instructions

### GPU-Accelerated Workloads
- **pow_gpu**: GPU-optimized SHA-256 mining using PyCUDA/CuPy
- **Important**: Default workloads run on CPU only, even on GPU instances
- See `GPU_OPTIMIZATION.md` for GPU acceleration details
- Use `pow_gpu` workload to leverage GPU on `g4dn.xlarge` instances

## Energy Estimation

Energy consumption is estimated using:
- **Base Power**: AWS published TDP values for each instance type
- **CPU Utilization**: Scaled by CloudWatch CPUUtilization metric
- **GPU Power**: nvidia-smi power draw for GPU instances
- **Duration**: Measured benchmark duration (5 minutes)
- **Formula**: Energy (Joules) = Power (Watts) × Time (seconds)

## Limitations

1. **FPGA Workloads**: Full FPGA workload implementation requires FPGA Developer AMI and AFI (Amazon FPGA Image)
2. **ZK-SNARK Simulation**: Default `zk` workload is simplified; use `zk_cloudzk` for FPGA acceleration via Cloud-ZK
3. **Cloud-ZK Setup**: Requires Cloud-ZK AFI ID and proper setup (see `CLOUD_ZK_INTEGRATION.md`)
4. **Energy Estimation**: Simplified model based on TDP; actual energy may vary
5. **Burstable Instances**: t3/t4g instances may experience CPU credit exhaustion during sustained workloads

## Troubleshooting

### Instance Launch Failures
- Check AWS region availability
- Verify IAM permissions
- Check service quotas (instance limits)

### SSH Connection Issues
- Ensure security group allows SSH (port 22)
- Check that key pair exists in AWS
- Wait for instances to fully initialize (60+ seconds)

### Metric Collection Failures
- CloudWatch metrics may take 1-2 minutes to appear
- GPU metrics require nvidia-smi on instance
- Ensure IAM role has CloudWatch read permissions

### Benchmark Timeouts
- Increase timeout in runner.py if needed
- Check instance status in AWS console
- Verify workloads are generating output


## Acknowledgments

- AWS EC2 for instance infrastructure
- Python libraries: boto3, pandas, seaborn, cryptography
- Cursor IDE

