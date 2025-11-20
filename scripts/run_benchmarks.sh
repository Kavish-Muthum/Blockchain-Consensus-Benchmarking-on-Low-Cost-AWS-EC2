#!/bin/bash
# Main execution script for blockchain consensus benchmarking
# Orchestrates: provision → benchmark → collect → visualize → cleanup

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

# Configuration
CONFIG_DIR="${PROJECT_DIR}/config"
RESULTS_DIR="${PROJECT_DIR}/results"
IAM_ROLE="${IAM_ROLE:-}"  # Set via environment variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Cleanup function
cleanup() {
    log_info "Running cleanup..."
    if [ -f "${PROJECT_DIR}/src/benchmarking/cleanup.py" ]; then
        python3 "${PROJECT_DIR}/src/benchmarking/cleanup.py" --config "${CONFIG_DIR}/instances.json" || true
    fi
}

# Set trap to ensure cleanup runs on exit
trap cleanup EXIT INT TERM

# Check Python dependencies
check_dependencies() {
    log_info "Checking Python dependencies..."
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    if [ ! -f "${PROJECT_DIR}/requirements.txt" ]; then
        log_error "requirements.txt not found"
        exit 1
    fi
    
    log_info "Installing Python dependencies..."
    pip3 install -q -r "${PROJECT_DIR}/requirements.txt" || {
        log_error "Failed to install dependencies"
        exit 1
    }
}

# Run benchmarks
run_benchmarks() {
    log_info "Starting benchmarks..."
    
    PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH}" python3 "${PROJECT_DIR}/src/benchmarking/runner.py" \
        --config "${CONFIG_DIR}/instances.json" \
        --workload-config "${CONFIG_DIR}/workloads.json" \
        --results "${RESULTS_DIR}" \
        ${IAM_ROLE:+--iam-role "$IAM_ROLE"}
    
    if [ $? -ne 0 ]; then
        log_error "Benchmarks failed"
        return 1
    fi
    
    log_info "Benchmarks completed successfully"
}

# Normalize and aggregate data
normalize_data() {
    log_info "Normalizing benchmark data..."
    
    PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH}" python3 "${PROJECT_DIR}/src/benchmarking/normalize.py" \
        --results "${RESULTS_DIR}"
    
    if [ $? -ne 0 ]; then
        log_error "Data normalization failed"
        return 1
    fi
    
    log_info "Data normalization completed"
}

# Generate tables
generate_tables() {
    log_info "Generating result tables..."
    
    PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH}" python3 "${PROJECT_DIR}/src/visualization/tables.py" \
        --summary "${RESULTS_DIR}/summary.csv" \
        --output "${RESULTS_DIR}/tables"
    
    if [ $? -ne 0 ]; then
        log_warn "Table generation failed (may be no data yet)"
        return 0
    fi
    
    log_info "Tables generated successfully"
}

# Generate graphs
generate_graphs() {
    log_info "Generating visualizations..."
    
    PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH}" python3 "${PROJECT_DIR}/src/visualization/graphs.py" \
        --summary "${RESULTS_DIR}/summary.csv" \
        --output "${RESULTS_DIR}/graphs"
    
    if [ $? -ne 0 ]; then
        log_warn "Graph generation failed (may be no data yet)"
        return 0
    fi
    
    log_info "Graphs generated successfully"
}

# Main execution
main() {
    log_info "Starting blockchain consensus benchmarking"
    log_info "Project directory: ${PROJECT_DIR}"
    log_info "Results directory: ${RESULTS_DIR}"
    
    if [ -n "$IAM_ROLE" ]; then
        log_info "Using IAM role: ${IAM_ROLE}"
    else
        log_warn "No IAM role specified. Using default AWS credentials."
    fi
    
    # Check dependencies
    check_dependencies
    
    # Create results directory
    mkdir -p "${RESULTS_DIR}/raw_logs"
    mkdir -p "${RESULTS_DIR}/tables"
    mkdir -p "${RESULTS_DIR}/graphs"
    
    # Run benchmarks
    if ! run_benchmarks; then
        log_error "Benchmark execution failed"
        exit 1
    fi
    
    # Check if we have results
    if [ ! -f "${RESULTS_DIR}/summary.csv" ]; then
        log_warn "No results found. Running normalization..."
        normalize_data
    fi
    
    # Normalize data
    normalize_data
    
    # Generate tables and graphs
    generate_tables
    generate_graphs
    
    # Generate PDF report
    log_info "Generating comprehensive PDF report..."
    PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH}" python3 "${PROJECT_DIR}/src/visualization/report.py" \
        --results "${RESULTS_DIR}" \
        --output "${RESULTS_DIR}/benchmark_report.pdf"
    
    if [ $? -eq 0 ]; then
        log_info "PDF report generated: ${RESULTS_DIR}/benchmark_report.pdf"
    else
        log_warn "PDF report generation failed (may be no data yet)"
    fi
    
    log_info "Benchmarking complete!"
    log_info "Results available in: ${RESULTS_DIR}"
    log_info "  - Raw logs: ${RESULTS_DIR}/raw_logs/"
    log_info "  - Summary: ${RESULTS_DIR}/summary.csv"
    log_info "  - Tables: ${RESULTS_DIR}/tables/"
    log_info "  - Graphs: ${RESULTS_DIR}/graphs/"
    log_info "  - PDF Report: ${RESULTS_DIR}/benchmark_report.pdf"
}

# Run main function
main

