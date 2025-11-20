#!/bin/bash
# Run benchmarks on ARM and x86 instances only (skip GPU/FPGA)
# Uses 8 vCPU instances for perfect comparison

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

echo "=========================================="
echo "Running Benchmarks: ARM vs x86 Only"
echo "=========================================="
echo ""
echo "Instance Types:"
echo "  - t4g.2xlarge (ARM) - 8 vCPU, 32GB RAM"
echo "  - t3.2xlarge (x86)  - 8 vCPU, 32GB RAM"
echo ""
echo "Workloads:"
echo "  - pow (Proof of Work)"
echo "  - pos (Proof of Stake)"
echo "  - bft (Byzantine Fault Tolerance)"
echo "  - zk (Zero-Knowledge Proofs)"
echo ""
echo "Total Tests: 2 instances × 4 workloads = 8 benchmarks"
echo ""
echo "Verbose output enabled - you will see:"
echo "  - Instance provisioning status"
echo "  - Workload deployment progress"
echo "  - Real-time workload output"
echo "  - Test completion summaries"
echo ""
echo "=========================================="
echo ""

# Run benchmarks with only ARM and x86
python3 src/benchmarking/runner.py \
    --only-arm-x86 \
    --config config/instances.json \
    --results results

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ All benchmarks completed successfully!"
    echo "=========================================="
    echo ""
    echo "Results saved in: results/raw_logs/"
    echo ""
    echo "Next steps:"
    echo "  1. Run normalization: python3 src/benchmarking/normalize.py"
    echo "  2. Generate graphs: python3 src/visualization/graphs.py"
    echo "  3. Generate tables: python3 src/visualization/tables.py"
    echo "  4. Generate PDF report: python3 src/visualization/report.py"
else
    echo ""
    echo "=========================================="
    echo "✗ Benchmarks failed!"
    echo "=========================================="
    echo ""
    echo "Check logs in: results/"
    exit 1
fi

