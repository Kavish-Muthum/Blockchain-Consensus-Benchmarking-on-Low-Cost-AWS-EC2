#!/bin/bash
# Setup script for Cloud-ZK on F1 instances
# This script prepares an F1 instance with Cloud-ZK FPGA acceleration

set -e

echo "Setting up Cloud-ZK on F1 instance..."

# Check if we're on F1 instance
INSTANCE_TYPE=$(curl -s http://169.254.169.254/latest/meta-data/instance-type)
if [[ ! "$INSTANCE_TYPE" =~ ^f1 ]]; then
    echo "Warning: This script is for F1 instances. Current instance: $INSTANCE_TYPE"
    exit 1
fi

# Install Rust
echo "Installing Rust..."
if ! command -v rustc &> /dev/null; then
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source $HOME/.cargo/env
else
    echo "Rust already installed"
fi

# Clone Cloud-ZK repository
echo "Cloning Cloud-ZK repository..."
CLOUDZK_DIR="/tmp/cloud-zk"
if [ ! -d "$CLOUDZK_DIR" ]; then
    git clone https://github.com/supranational/cloud-zk.git "$CLOUDZK_DIR" || {
        echo "Error: Failed to clone Cloud-ZK repository"
        echo "Make sure git is installed and network is available"
        exit 1
    }
else
    echo "Cloud-ZK directory already exists, updating..."
    cd "$CLOUDZK_DIR"
    git pull || echo "Warning: Could not update repository"
fi

# Build Cloud-ZK library
echo "Building Cloud-ZK Rust library (this may take 10-30 minutes)..."
cd "$CLOUDZK_DIR"
cargo build --release || {
    echo "Error: Failed to build Cloud-ZK library"
    echo "Check dependencies and try again"
    exit 1
}

echo "Cloud-ZK setup complete!"
echo ""
echo "Next steps:"
echo "1. Get Cloud-ZK AFI ID from the repository or AWS Marketplace"
echo "2. Load AFI: sudo fpga-load-local-image -S 0 -I <afi-id>"
echo "3. Verify: fpga-describe-local-image-slots -H"
echo "4. Run benchmark: python3 src/workloads/zk_cloudzk.py"

