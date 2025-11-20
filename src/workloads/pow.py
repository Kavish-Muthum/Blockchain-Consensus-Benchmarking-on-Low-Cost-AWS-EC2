#!/usr/bin/env python3
"""
Proof of Work (PoW) workload using SHA-256 mining.
Fixed difficulty target for consistent workload across instances.
"""
import hashlib
import json
import sys
import time
from datetime import datetime

def mine_block(nonce, block_template, difficulty_target):
    """Attempt to mine a block with given nonce."""
    block_data = f"{block_template}{nonce}".encode()
    block_hash = hashlib.sha256(block_data).hexdigest()
    return block_hash, block_hash.startswith(difficulty_target)

def main():
    # Configuration from command line args or defaults
    warmup_seconds = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    measurement_seconds = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    difficulty_target = sys.argv[3] if len(sys.argv) > 3 else "00000"
    block_template = sys.argv[4] if len(sys.argv) > 4 else "BlockTemplate_2024_Benchmark_Consensus_Research"
    
    hashes_attempted = 0
    nonce = 0
    start_time = time.time()
    
    # Warmup period
    warmup_end = start_time + warmup_seconds
    print(f"WARMUP: Starting {warmup_seconds}s warmup...", file=sys.stderr)
    while time.time() < warmup_end:
        block_hash, found = mine_block(nonce, block_template, difficulty_target)
        hashes_attempted += 1
        nonce += 1
        if nonce % 10000 == 0:
            print(f"WARMUP: {hashes_attempted} hashes attempted", file=sys.stderr)
    
    # Reset counters for measurement period
    measurement_start = time.time()
    measurement_end = measurement_start + measurement_seconds
    hashes_attempted = 0
    last_log_time = measurement_start
    log_interval = 1.0  # Log every second
    
    print(f"MEASUREMENT: Starting {measurement_seconds}s measurement period...", file=sys.stderr)
    
    while time.time() < measurement_end:
        current_time = time.time()
        block_hash, found = mine_block(nonce, block_template, difficulty_target)
        hashes_attempted += 1
        nonce += 1
        
        # Log at regular intervals
        if current_time - last_log_time >= log_interval:
            elapsed = current_time - measurement_start
            log_entry = {
                "work_unit": "hash",
                "count": hashes_attempted,
                "timestamp": current_time,
                "difficulty_target": difficulty_target,
                "elapsed_seconds": elapsed,
                "hashes_per_second": hashes_attempted / elapsed if elapsed > 0 else 0
            }
            print(json.dumps(log_entry), flush=True)
            last_log_time = current_time
    
    # Final summary
    final_time = time.time()
    total_elapsed = final_time - measurement_start
    final_summary = {
        "work_unit": "hash",
        "total_count": hashes_attempted,
        "measurement_duration_seconds": total_elapsed,
        "hashes_per_second": hashes_attempted / total_elapsed if total_elapsed > 0 else 0,
        "difficulty_target": difficulty_target,
        "block_template": block_template,
        "measurement_start": measurement_start,
        "measurement_end": final_time
    }
    print(json.dumps({"final": final_summary}), flush=True)

if __name__ == "__main__":
    main()

