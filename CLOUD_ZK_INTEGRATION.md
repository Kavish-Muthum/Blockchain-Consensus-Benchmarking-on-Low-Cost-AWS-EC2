# Cloud-ZK Integration Guide

## Overview

**Cloud-ZK** is an open-source toolkit that provides FPGA-accelerated zero-knowledge proof capabilities on AWS F1 instances. It includes:
- Pre-built AFI for BLS12-377 Multiscalar Multiplication (MSM) - a key component in zk-SNARKs
- Rust library for FPGA acceleration and data transfer
- Free to use and optimized for AWS EC2 F1 instances

## Benefits of Using Cloud-ZK

1. **No Custom FPGA Design Needed**: Pre-built AFI eliminates months of FPGA development
2. **Production-Ready**: Already tested and optimized
3. **Free and Open Source**: No licensing costs
4. **BLS12-377 MSM**: Directly accelerates a critical zk-SNARK component
5. **Rust Integration**: Modern, safe interface for FPGA communication

## Cloud-ZK Resources

- **GitHub**: https://github.com/supranational/cloud-zk
- **Documentation**: Check the repository for latest setup instructions
- **AFI ID**: Provided in the repository (or AWS Marketplace)

## Integration Steps

### Step 1: Get Cloud-ZK AFI

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/supranational/cloud-zk.git
   cd cloud-zk
   ```

2. **Find AFI ID**:
   - Check repository README for published AFI ID
   - Or search AWS Marketplace for "Cloud-ZK"
   - Or create AFI from provided design (if source available)

3. **Note the AFI ID**: You'll need this to load onto F1 instances

### Step 2: Setup F1 Instance with Cloud-ZK

1. **Launch F1 Instance**:
   ```bash
   # Use FPGA Developer AMI
   # Instance type: f1.2xlarge (or f1.4xlarge, f1.16xlarge)
   ```

2. **Install Cloud-ZK Rust Library**:
   ```bash
   # On F1 instance
   git clone https://github.com/supranational/cloud-zk.git
   cd cloud-zk
   # Follow installation instructions from repository
   ```

3. **Load Cloud-ZK AFI**:
   ```bash
   # Load the AFI onto FPGA slot 0
   sudo fpga-load-local-image -S 0 -I <cloud-zk-afi-id>
   
   # Verify AFI is loaded
   fpga-describe-local-image-slots -H
   ```

### Step 3: Install Rust and Dependencies

```bash
# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install Cloud-ZK dependencies
# Follow Cloud-ZK repository instructions
```

### Step 4: Build Rust Bindings

```bash
# Build Cloud-ZK Rust library
cd cloud-zk
cargo build --release

# This provides Rust bindings for FPGA acceleration
```

## Integration with Benchmark Framework

### Modified ZK Workload

The benchmark framework includes `src/workloads/zk_cloudzk.py` which:
- Uses Cloud-ZK Rust library for FPGA acceleration
- Calls BLS12-377 MSM operations on FPGA
- Falls back to software if FPGA unavailable
- Measures FPGA vs CPU performance

### Usage

1. **Deploy Cloud-ZK on F1 Instance**:
   - AFI loaded via user data script or manually
   - Rust library installed

2. **Run Benchmark**:
   ```bash
   # The benchmark will automatically detect Cloud-ZK if available
   python3 src/benchmarking/runner.py --instance f1.2xlarge --workload zk_cloudzk
   ```

3. **Performance Comparison**:
   - Benchmark compares FPGA-accelerated vs CPU-only performance
   - Measures throughput (proofs/sec)
   - Measures energy efficiency (Joules/proof)

## User Data Script Integration

The provision script can be modified to automatically:
1. Install Rust and Cloud-ZK
2. Load Cloud-ZK AFI
3. Build Rust library

Add to `src/benchmarking/provision.py` user data script for F1 instances.

## Expected Performance Improvements

Cloud-ZK FPGA acceleration should provide:
- **10-100x speedup** for MSM operations (depending on workload)
- **Lower energy per operation** (FPGA is more efficient than CPU for this)
- **Better scalability** for larger proof sizes

## Troubleshooting

### AFI Not Loading
- Verify AFI ID is correct
- Check FPGA Developer AMI subscription
- Ensure F1 instance quota is sufficient

### Rust Library Issues
- Verify Rust is installed correctly
- Check Cloud-ZK repository for latest dependencies
- Ensure FPGA is loaded before building library

### Performance Not Improving
- Verify AFI is actually loaded: `fpga-describe-local-image-slots -H`
- Check that workload is using FPGA path (check logs)
- Ensure workload size is sufficient to benefit from FPGA

## Next Steps

1. **Get Cloud-ZK AFI ID**: From repository or AWS Marketplace
2. **Test Locally**: Load AFI and verify it works
3. **Integrate with Benchmark**: Use modified workload
4. **Compare Results**: FPGA vs CPU performance and efficiency

## Resources

- **Cloud-ZK GitHub**: https://github.com/supranational/cloud-zk
- **AWS F1 Documentation**: https://docs.aws.amazon.com/ec2/latest/userguide/ec2-fpga-instances.html
- **BLS12-377 Curve**: Research paper/documentation
- **MSM Algorithm**: Multiscalar Multiplication documentation

