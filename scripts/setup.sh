#!/bin/bash
# Environment setup script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

echo "Setting up blockchain consensus benchmarking environment..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python version: $(python3 --version)"

# Create virtual environment (optional but recommended)
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate 2>/dev/null || true

# Install dependencies
echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Verify AWS credentials
echo "Checking AWS credentials..."
if python3 -c "import boto3; boto3.Session().get_credentials()" 2>/dev/null; then
    echo "AWS credentials found"
else
    echo "Warning: AWS credentials not found. Make sure they are configured."
fi

# Make scripts executable
chmod +x scripts/*.sh
chmod +x src/workloads/*.py
chmod +x src/benchmarking/*.py
chmod +x src/visualization/*.py

echo "Setup complete!"
echo ""
echo "To run benchmarks:"
echo "  export IAM_ROLE='your-iam-role-name'  # Optional"
echo "  ./scripts/run_benchmarks.sh"

