# Amazon FPGA Image (AFI) Setup Guide

## What is an AFI?

An **Amazon FPGA Image (AFI)** is a compiled FPGA design that can be loaded onto AWS F1 instances (like f1.2xlarge). Think of it as a "binary" for FPGAs - it's the hardware configuration that programs the FPGA with your specific logic.

## Why AFI is Required for F1 Instances

Unlike regular EC2 instances that run software, F1 instances need:
1. **FPGA Developer AMI**: Special AMI with FPGA development tools
2. **AFI (Amazon FPGA Image)**: The compiled FPGA bitstream/design
3. **AFI Loader**: Tool to load the AFI onto the FPGA hardware

Without an AFI loaded, the FPGA hardware on f1.2xlarge is unprogrammed and can't execute any FPGA-accelerated workloads.

## AFI Setup Process

### Step 1: Subscribe to FPGA Developer AMI

1. Go to AWS Marketplace: https://aws.amazon.com/marketplace
2. Search for "FPGA Developer AMI"
3. Click "Continue to Subscribe"
4. Accept terms and subscribe
5. Wait for subscription activation (usually immediate)

### Step 2: Create AFI from Design

There are two approaches:

#### Option A: Use Pre-built AFI (Easier for Benchmarking)

Some vendors provide pre-built AFIs for common workloads:
- Search AWS Marketplace for "FPGA" and your workload type
- Use publicly available AFIs (if compatible with your workload)

#### Option B: Build Custom AFI (For Custom Workloads)

This requires:
1. **FPGA Development Environment**:
   - Xilinx Vivado Design Suite (provided in FPGA Developer AMI)
   - FPGA design files (.v, .vhd, or high-level language)
   
2. **Development Process**:
   ```
   Design → Synthesize → Place & Route → Generate .bit file → Create AFI
   ```

3. **Create AFI**:
   ```bash
   # On FPGA Developer AMI instance
   $ fpga-create-afi \
       --afi-name my-benchmark-afi \
       --afi-description "AFI for blockchain benchmarking" \
       --afi-fpga-image-id <local-fpga-image-id> \
       --afi-s3-bucket <your-s3-bucket> \
       --afi-s3-dcp-key <path/to/dcp> \
       --afi-s3-logs-key <path/to/logs>
   ```

4. **Wait for AFI Creation**: 
   - Takes 3-10 hours typically
   - Check status: `aws ec2 describe-fpga-images --fpga-image-ids <afi-id>`

### Step 3: Load AFI on F1 Instance

Once you have an AFI ID, load it onto your F1 instance:

```bash
# SSH into your F1 instance (FPGA Developer AMI)
$ sudo fpga-load-local-image -S 0 -I <afi-id>

# Verify AFI is loaded
$ fpga-describe-local-image-slots -H
```

### Step 4: Run FPGA-Accelerated Workload

After loading the AFI, you can:
- Access FPGA logic through AWS FPGA Shell Interface
- Use vendor SDKs (e.g., Xilinx SDAccel)
- Run your FPGA-accelerated application

## AFI Quotas

From your AWS Service Quotas console:
- **Amazon FPGA images (AFIs)**: Default quota is **100**
- Quota Code: `L-8FBBDF0C`
- This is the number of AFIs you can **own**, not load simultaneously

## AFI States

AFIs have different states:
- **pending**: Being created
- **available**: Ready to use
- **failed**: Creation failed
- **unavailable**: Can't be used (deleted or suspended)

## For Blockchain Benchmarking

### Current Challenge

The benchmark workload (`zk.py`) is a **software simulation** of ZK-SNARK proofs, not a true FPGA-accelerated implementation. To use FPGA effectively, you would need:

1. **Hardware-Accelerated ZK Circuit**: 
   - Design FPGA logic for polynomial operations
   - Implement pairing operations in hardware
   - Accelerate proof generation steps

2. **Custom AFI Creation**:
   - Synthesize ZK circuit to FPGA bitstream
   - Create AFI from bitstream
   - Load AFI on f1.2xlarge instance

3. **Modified Workload**:
   - Use FPGA shell interface instead of CPU
   - Leverage hardware acceleration for proof generation

### Simplified Approach for Benchmarking

Since creating a custom ZK-SNARK FPGA design is complex, the current benchmark:

1. **Uses FPGA Developer AMI**: To ensure proper instance setup
2. **Runs Software Simulation**: The ZK workload runs on CPU, not FPGA
3. **Measures CPU Power**: Energy estimation uses CPU power, not FPGA power

This still provides value because:
- Tests FPGA instance's CPU performance
- Shows baseline performance before FPGA acceleration
- Demonstrates that FPGA instances can run general workloads

## Alternative: Skip FPGA for Benchmarking

If FPGA setup is too complex, you can:

1. **Remove f1.2xlarge from benchmarks**: Only test t4g.micro, t3.micro, g4dn.xlarge
2. **Modify instance config**: Comment out f1.2xlarge in `config/instances.json`
3. **Run benchmarks**: The runner will skip unavailable instances automatically

## Recommended Setup for Full FPGA Benchmarking

If you want true FPGA-accelerated benchmarking:

### 1. Start with Pre-built AFI
```bash
# List available AFIs
aws ec2 describe-fpga-images --owners amazon

# Example: Use a simple test AFI
aws ec2 describe-fpga-images --fpga-image-ids afi-0123456789abcdef0
```

### 2. Launch F1 Instance with FPGA Developer AMI
```bash
# Use AMI ID from Marketplace subscription
# Example: ami-0cb1b6ae2ff99f8bf (FPGA Developer AMI 1.18.0)
```

### 3. Load AFI and Test
```bash
# On F1 instance
sudo fpga-load-local-image -S 0 -I afi-xxxxx

# Verify
fpga-describe-local-image-slots -H
```

### 4. Integrate with Benchmark Workload
Modify `src/workloads/zk.py` to:
- Call FPGA acceleration via shell interface
- Measure FPGA power consumption separately
- Report FPGA-accelerated proof generation metrics

## Current Implementation Status

The current benchmark implementation:
- ✅ Can provision f1.2xlarge instances (if quota allows)
- ✅ Uses FPGA Developer AMI pattern matching
- ⚠️ Does NOT load an AFI (FPGA runs unprogrammed)
- ⚠️ Runs software-only workloads on CPU
- ⚠️ Energy estimation doesn't include FPGA power

## Resources

- **AWS F1 Documentation**: https://docs.aws.amazon.com/ec2/latest/userguide/ec2-fpga-instances.html
- **FPGA Developer AMI**: https://aws.amazon.com/marketplace/pp/prodview-ubjg3oa5n4hbo
- **Creating AFIs**: https://github.com/aws/aws-fpga/blob/master/sdk/userspace/fpga_mgmt_tools/README.md
- **AFI Management**: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/efs-volumes.html#describe-fpga-images

## Summary

**AFI (Amazon FPGA Image)** is the compiled FPGA design that must be loaded onto F1 instances to enable FPGA hardware acceleration. For benchmarking:

1. **Simple Approach**: Skip f1.2xlarge or run CPU-only workloads
2. **Full Approach**: Create/acquire AFI, load it, and modify workloads to use FPGA acceleration

The current benchmark framework is designed to work with or without FPGA acceleration - it will gracefully handle unavailable FPGA instances and provide useful CPU-based benchmarks.

