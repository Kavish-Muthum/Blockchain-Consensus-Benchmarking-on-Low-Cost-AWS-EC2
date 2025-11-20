#!/bin/bash
# Run optimized benchmarks only (hardware-specific implementations)
# This shows best-case performance for each hardware type

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

echo "Running OPTIMIZED benchmarks (hardware-specific implementations)"
echo "This shows best-case performance per hardware type."
echo ""

# CPU instances: Use standard workloads (already optimized for CPU)
echo "Running on CPU instances..."
python3 src/benchmarking/runner.py --instance t4g.micro --workload pow
python3 src/benchmarking/runner.py --instance t3.micro --workload pow

# GPU instances: Use GPU-accelerated workloads
echo "Running GPU-accelerated workloads..."
python3 src/benchmarking/runner.py --instance g4dn.xlarge --workload pow_gpu || {
    echo "GPU workload failed, falling back to CPU"
    python3 src/benchmarking/runner.py --instance g4dn.xlarge --workload pow
}

# FPGA instances: Use FPGA-accelerated workloads
echo "Running FPGA-accelerated workloads..."
python3 src/benchmarking/runner.py --instance f1.2xlarge --workload zk_cloudzk || {
    echo "FPGA workload failed, falling back to CPU"
    python3 src/benchmarking/runner.py --instance f1.2xlarge --workload zk
}

echo ""
echo "Optimized benchmarks complete!"
echo "Results in: results/raw_logs/"
echo ""
echo "Note: These show best-case performance with hardware-specific optimization"

