#!/usr/bin/env python3
"""
Byzantine Fault Tolerance (BFT) workload simulating PBFT consensus.
Fixed node count, message sizes, and consensus logic for consistency.
"""
import json
import sys
import time
import hashlib
from typing import List, Dict

class PBFTNode:
    """Simulates a single PBFT node."""
    def __init__(self, node_id, total_nodes):
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.sequence_number = 0
        self.prepared = False
        self.committed = False
        
    def prepare(self, message_hash, sequence):
        """Prepare phase."""
        self.sequence_number = sequence
        self.prepared = True
        return True
    
    def commit(self, message_hash, sequence):
        """Commit phase."""
        if self.prepared and self.sequence_number == sequence:
            self.committed = True
            return True
        return False
    
    def reset(self):
        """Reset for next round."""
        self.prepared = False
        self.committed = False

class PBFTCluster:
    """Simulates a PBFT cluster with multiple nodes."""
    def __init__(self, node_count, byzantine_tolerance):
        self.node_count = node_count
        self.byzantine_tolerance = byzantine_tolerance
        self.required_votes = (2 * byzantine_tolerance) + 1
        self.nodes = [PBFTNode(i, node_count) for i in range(node_count)]
        
    def run_consensus_round(self, message):
        """Run a single consensus round."""
        message_hash = hashlib.sha256(message.encode()).hexdigest()
        sequence = self.nodes[0].sequence_number + 1
        
        # Prepare phase - need (2f+1) prepare votes
        prepare_votes = 0
        for node in self.nodes:
            if node.prepare(message_hash, sequence):
                prepare_votes += 1
        
        if prepare_votes < self.required_votes:
            return False
        
        # Commit phase - need (2f+1) commit votes
        commit_votes = 0
        for node in self.nodes:
            if node.commit(message_hash, sequence):
                commit_votes += 1
        
        if commit_votes >= self.required_votes:
            # Consensus reached
            for node in self.nodes:
                node.reset()
            return True
        
        return False

def main():
    # Configuration from command line args or defaults
    warmup_seconds = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    measurement_seconds = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    node_count = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    byzantine_tolerance = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    message_size = int(sys.argv[5]) if len(sys.argv) > 5 else 1024
    
    # Create PBFT cluster
    cluster = PBFTCluster(node_count, byzantine_tolerance)
    
    rounds_completed = 0
    round_number = 0
    start_time = time.time()
    
    # Generate fixed-size message
    message = "B" * message_size
    
    # Warmup period
    warmup_end = start_time + warmup_seconds
    print(f"WARMUP: Starting {warmup_seconds}s warmup with {node_count} nodes, {byzantine_tolerance} Byzantine tolerance...", file=sys.stderr)
    while time.time() < warmup_end:
        if cluster.run_consensus_round(f"{message}_{round_number}"):
            rounds_completed += 1
        round_number += 1
        if round_number % 100 == 0:
            print(f"WARMUP: {round_number} rounds attempted", file=sys.stderr)
    
    # Reset counters for measurement period
    measurement_start = time.time()
    measurement_end = measurement_start + measurement_seconds
    rounds_completed = 0
    round_number = 0
    last_log_time = measurement_start
    log_interval = 1.0  # Log every second
    
    print(f"MEASUREMENT: Starting {measurement_seconds}s measurement period...", file=sys.stderr)
    
    while time.time() < measurement_end:
        current_time = time.time()
        if cluster.run_consensus_round(f"{message}_{round_number}"):
            rounds_completed += 1
        round_number += 1
        
        # Log at regular intervals
        if current_time - last_log_time >= log_interval:
            elapsed = current_time - measurement_start
            log_entry = {
                "work_unit": "round",
                "count": rounds_completed,
                "timestamp": current_time,
                "nodes": node_count,
                "byzantine_tolerance": byzantine_tolerance,
                "message_size_bytes": message_size,
                "elapsed_seconds": elapsed,
                "rounds_per_second": rounds_completed / elapsed if elapsed > 0 else 0
            }
            print(json.dumps(log_entry), flush=True)
            last_log_time = current_time
    
    # Final summary
    final_time = time.time()
    total_elapsed = final_time - measurement_start
    final_summary = {
        "work_unit": "round",
        "total_count": rounds_completed,
        "measurement_duration_seconds": total_elapsed,
        "rounds_per_second": rounds_completed / total_elapsed if total_elapsed > 0 else 0,
        "nodes": node_count,
        "byzantine_tolerance": byzantine_tolerance,
        "message_size_bytes": message_size,
        "measurement_start": measurement_start,
        "measurement_end": final_time
    }
    print(json.dumps({"final": final_summary}), flush=True)

if __name__ == "__main__":
    main()

