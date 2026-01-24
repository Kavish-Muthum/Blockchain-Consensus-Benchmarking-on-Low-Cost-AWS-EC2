# Blockchain Consensus Benchmarking on Low-Cost AWS EC2

This project benchmarks major blockchain consensus workloads on the lowest-cost AWS EC2 instances from each hardware category, measuring performance and resource/energy efficiency.

## Overview

The benchmark tests four consensus algorithms across four EC2 instance types:
- **Proof of Work (PoW)**: SHA-256 mining
- **Proof of Stake (PoS)**: Ed25519 signature verification
- **Byzantine Fault Tolerance (BFT)**: PBFT consensus simulation
- **Zero-Knowledge Proofs (ZK)**: ZK-SNARK proof generation

### Instance Types Tested

| Instance Type | Architecture | Category | vCPU | Memory | Estimated TDP | Hourly Cost (us-east-1) |
|--------------|-------------|----------|------|--------|---------------|-------------------------|
| t4g.small    | ARM (arm64) | ARM      | 2    | 2 GB   | 6W            | $0.0168                |
| t3.small     | x86_64      | x86      | 2    | 2 GB   | 7W            | $0.0208                |
| g4dn.xlarge  | x86_64      | GPU      | 4    | 16 GB  | 200W          | $0.526                 |
| f1.2xlarge   | x86_64      | FPGA     | 8    | 122 GB | 150W          | $1.65                  |

**Note**: ARM and x86 instances have identical specs (2 vCPU, 2GB RAM) for direct comparison. GPU and FPGA instances are normalized by vCPU in analysis.

## Setup

### Prerequisites
- Python 3.8+
- AWS account with EC2 and CloudWatch access
- AWS credentials configured (via `~/.aws/credentials` or IAM role)
- IAM permissions: EC2 (launch/terminate), CloudWatch (read), IAM (read roles if using IAM roles)

### Installation

```bash
git clone <repository-url>
cd Blockchain-Consensus-Benchmarking-on-Low-Cost-AWS-EC2
./scripts/setup.sh
aws configure  # if not using IAM role
```

## Usage

### Running Benchmarks

```bash
# Using IAM role (recommended)
export IAM_ROLE='your-iam-role-name'
./scripts/run_benchmarks.sh

# Using default AWS credentials
./scripts/run_benchmarks.sh
```

This runs CPU-only workloads on all instances for fair hardware comparison. The script will:
1. Provision EC2 instances for each instance type
2. Run all workloads on each instance
3. Collect CloudWatch metrics and custom metrics (GPU/FPGA)
4. Normalize and aggregate results
5. Generate comparison tables and visualizations
6. Clean up all instances

### Running Individual Benchmarks

```bash
python3 src/benchmarking/runner.py \
    --instance t3.micro \
    --workload pow \
    --iam-role your-iam-role-name
```

### Monitoring Progress

```bash
./scripts/monitor_progress.sh
# or
tail -f results/benchmark_progress.log
```

### Cleanup

```bash
python3 src/benchmarking/cleanup.py
```

## Results

Results are generated in the `results/` directory:
- **`summary.csv`** / **`summary.json`**: Aggregated results
- **`raw_logs/`**: Raw benchmark output per instance/workload
- **`tables/`**: Markdown comparison tables
- **`graphs/`**: Visualization graphs (PNG format)
- **`benchmark_report.pdf`**: Comprehensive PDF report

## Workload Details

- **PoW**: SHA-256 hashing with fixed difficulty target (single-threaded)
- **PoS**: Ed25519 signature verification with pre-generated test pairs
- **BFT**: PBFT consensus simulation (4 nodes, 1 Byzantine tolerance)
- **ZK**: Simplified ZK-SNARK simulation (CPU-only) or Cloud-ZK FPGA-accelerated version (see `CLOUD_ZK_INTEGRATION.md`)

## Energy Estimation

Energy consumption is estimated using:
- **Base Power**: AWS TDP values for each instance type
- **CPU Utilization**: Scaled by CloudWatch CPUUtilization metric
- **GPU Power**: nvidia-smi power draw for GPU instances
- **Duration**: 5-minute measurement window
- **Formula**: Energy (Joules) = Power (Watts) × Time (seconds)

## Comparability Strategy

To ensure fair comparison:
1. Fixed workload parameters across all instances
2. Exact 5-minute measurement window with 30-second warmup
3. Consistent environment (AMI families, dependency versions)
4. Normalization by vCPU for different core counts
5. Energy calculated using AWS TDP values

## Limitations

1. **FPGA Workloads**: Requires FPGA Developer AMI and AFI (see `FPGA_AFI_SETUP.md`)
2. **ZK-SNARK Simulation**: Default `zk` workload is simplified; use `zk_cloudzk` for FPGA acceleration
3. **Energy Estimation**: Simplified model based on TDP; actual energy may vary
4. **Burstable Instances**: t3/t4g instances may experience CPU credit exhaustion during sustained workloads

## Troubleshooting

- **Instance Launch Failures**: Check AWS region availability, IAM permissions, service quotas
- **SSH Connection Issues**: Ensure security group allows SSH (port 22), key pair exists, wait 60+ seconds for initialization
- **Metric Collection Failures**: CloudWatch metrics may take 1-2 minutes to appear; GPU metrics require nvidia-smi
- **Benchmark Timeouts**: Increase timeout in runner.py if needed, check instance status in AWS console

## Acknowledgments

- AWS EC2 for instance infrastructure
- Python libraries: boto3, pandas, seaborn, cryptography

---

## Final Research Paper

The final version of this research is documented in `annotated-Hardware_Optimizations_for_Energy_Efficiency_of_Cryptocurrencies-2.pdf`. This paper expands on the baseline benchmarking in this repository by considering GPU software optimizations during execution through GPU-specific implementations, including CUDA-accelerated workloads and hardware-specific optimizations.

**Note**: This repository contains the baseline benchmarking code. The GPU-optimized implementations referenced in the paper are not included in this repository. **To access the GPU-optimized code used in the final research, please contact me.**
