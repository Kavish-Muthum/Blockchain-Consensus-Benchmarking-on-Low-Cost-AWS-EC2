#!/bin/bash
# Build AFI from Verilog design
# This script creates an AFI from the ZK arithmetic circuit

set -e

echo "Building AFI for ZK Arithmetic Circuit..."

# Check if we're on FPGA Developer AMI
if [ ! -d "$AWS_FPGA_REPO_DIR" ]; then
    echo "Error: AWS_FPGA_REPO_DIR not set. Are you on FPGA Developer AMI?"
    exit 1
fi

PROJECT_DIR=$(pwd)
DESIGN_NAME="zk_arithmetic"
BUILD_DIR="$PROJECT_DIR/build"
LOG_DIR="$PROJECT_DIR/logs"

mkdir -p $BUILD_DIR $LOG_DIR

# Source AWS FPGA setup
source $AWS_FPGA_REPO_DIR/sdaccel_setup.sh

# Step 1: Create Vivado project (simplified)
echo "Creating Vivado project..."

# Use Xilinx Vivado to synthesize and place & route
# This is a simplified command - full implementation would use makefiles
vivado -mode batch -source create_project.tcl -log $LOG_DIR/create_project.log

# Step 2: Synthesize design
echo "Synthesizing design..."
vivado -mode batch -source synth.tcl -log $LOG_DIR/synth.log

# Step 3: Place and Route
echo "Placing and routing..."
vivado -mode batch -source implement.tcl -log $LOG_DIR/implement.log

# Step 4: Generate bitstream
echo "Generating bitstream..."
vivado -mode batch -source bitstream.tcl -log $LOG_DIR/bitstream.log

# Step 5: Create AFI
echo "Creating AFI..."
# This requires:
# - DCP file from Vivado
# - S3 bucket for AFI storage
# - Logs location

# Example command (adjust paths as needed):
# $SDACCEL_DIR/tools/create_sdaccel_afi.sh \
#     -xclbin=<path_to_xclbin> \
#     -o=<afi_name> \
#     -s3_bucket=<your_s3_bucket> \
#     -s3_dcp_key=<path/to/dcp> \
#     -s3_logs_key=<path/to/logs>

echo "Build complete! Check logs for details."
echo "Next step: Upload DCP to S3 and create AFI using AWS CLI"

