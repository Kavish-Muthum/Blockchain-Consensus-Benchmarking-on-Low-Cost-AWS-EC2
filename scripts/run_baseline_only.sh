#!/bin/bash
# Run baseline benchmarks only (same algorithm on all instances)
# This ensures fair hardware comparison with identical workloads

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

echo "Running BASELINE benchmarks only (same algorithm on all instances)"
echo "This ensures fair hardware comparison."
echo ""

# Run all standard workloads (CPU-only versions)
python3 src/benchmarking/runner.py \
    --instance t4g.micro --workload pow \
    --instance t4g.micro --workload pos \
    --instance t4g.micro --workload bft \
    --instance t4g.micro --workload zk

python3 src/benchmarking/runner.py \
    --instance t3.micro --workload pow \
    --instance t3.micro --workload pos \
    --instance t3.micro --workload bft \
    --instance t3.micro --workload zk

python3 src/benchmarking/runner.py \
    --instance g4dn.xlarge --workload pow \
    --instance g4dn.xlarge --workload pos \
    --instance g4dn.xlarge --workload bft \
    --instance g4dn.xlarge --workload zk

# Note: FPGA instances will skip if unavailable, but would run CPU versions

echo ""
echo "Baseline benchmarks complete!"
echo "Results in: results/raw_logs/"
echo ""
echo "To compare with optimized versions, run:"
echo "  python3 src/benchmarking/runner.py --instance g4dn.xlarge --workload pow_gpu"
echo "  python3 src/benchmarking/runner.py --instance f1.2xlarge --workload zk_cloudzk"

