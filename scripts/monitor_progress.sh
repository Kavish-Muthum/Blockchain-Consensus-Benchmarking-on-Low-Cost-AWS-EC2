#!/bin/bash
# Monitor benchmark progress in real-time
# Usage: ./scripts/monitor_progress.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="${PROJECT_DIR}/results/benchmark_progress.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=== Benchmark Progress Monitor ===${NC}"
echo -e "${GREEN}Monitoring log file: ${LOG_FILE}${NC}"
echo ""

# Check if log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo -e "${YELLOW}Warning: Log file does not exist yet.${NC}"
    echo -e "${YELLOW}Waiting for benchmark to start...${NC}"
    echo ""
    
    # Wait for log file to be created
    while [ ! -f "$LOG_FILE" ]; do
        sleep 1
    done
    
    echo -e "${GREEN}Log file created! Starting monitor...${NC}"
    echo ""
fi

# Use tail -f to follow the log file with color highlighting
tail -f "$LOG_FILE" | while IFS= read -r line; do
    # Color code different log levels and progress indicators
    if echo "$line" | grep -q "ERROR"; then
        echo -e "${RED}$line${NC}"
    elif echo "$line" | grep -q "WARN"; then
        echo -e "${YELLOW}$line${NC}"
    elif echo "$line" | grep -q "✓"; then
        echo -e "${GREEN}$line${NC}"
    elif echo "$line" | grep -q "Progress:"; then
        echo -e "${BLUE}$line${NC}"
    elif echo "$line" | grep -q "BENCHMARK SUITE\|ALL BENCHMARKS\|==="; then
        echo -e "${CYAN}$line${NC}"
    elif echo "$line" | grep -q "\[.*/.*\]"; then
        echo -e "${GREEN}$line${NC}"
    else
        echo "$line"
    fi
done

