#!/usr/bin/env python3
"""
Proof of Stake (PoS) workload using Ed25519 signature verification.
Pre-generated test messages and signatures for consistency.
"""
import json
import sys
import time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def generate_test_data(num_pairs=1000):
    """Generate test message/signature pairs."""
    test_pairs = []
    for i in range(num_pairs):
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        message = f"TestMessage_{i}_Benchmark_2024".encode()
        signature = private_key.sign(message)
        
        # Serialize public key for storage
        pub_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        test_pairs.append({
            "message": message,
            "signature": signature,
            "public_key": pub_key_bytes
        })
    return test_pairs

def verify_signature(message, signature, public_key_bytes):
    """Verify a signature."""
    try:
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(signature, message)
        return True
    except Exception:
        return False

def main():
    # Configuration from command line args or defaults
    warmup_seconds = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    measurement_seconds = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    
    # Generate test data once
    print("GENERATING: Creating test message/signature pairs...", file=sys.stderr)
    test_pairs = generate_test_data(1000)
    print(f"GENERATED: {len(test_pairs)} test pairs ready", file=sys.stderr)
    
    signatures_verified = 0
    pair_index = 0
    start_time = time.time()
    
    # Warmup period
    warmup_end = start_time + warmup_seconds
    print(f"WARMUP: Starting {warmup_seconds}s warmup...", file=sys.stderr)
    while time.time() < warmup_end:
        pair = test_pairs[pair_index % len(test_pairs)]
        if verify_signature(pair["message"], pair["signature"], pair["public_key"]):
            signatures_verified += 1
        pair_index += 1
        if pair_index % 1000 == 0:
            print(f"WARMUP: {pair_index} signatures verified", file=sys.stderr)
    
    # Reset counters for measurement period
    measurement_start = time.time()
    measurement_end = measurement_start + measurement_seconds
    signatures_verified = 0
    pair_index = 0
    last_log_time = measurement_start
    log_interval = 1.0  # Log every second
    
    print(f"MEASUREMENT: Starting {measurement_seconds}s measurement period...", file=sys.stderr)
    
    while time.time() < measurement_end:
        current_time = time.time()
        pair = test_pairs[pair_index % len(test_pairs)]
        if verify_signature(pair["message"], pair["signature"], pair["public_key"]):
            signatures_verified += 1
        pair_index += 1
        
        # Log at regular intervals
        if current_time - last_log_time >= log_interval:
            elapsed = current_time - measurement_start
            log_entry = {
                "work_unit": "signature",
                "count": signatures_verified,
                "timestamp": current_time,
                "algorithm": "ed25519",
                "key_size": 256,
                "elapsed_seconds": elapsed,
                "signatures_per_second": signatures_verified / elapsed if elapsed > 0 else 0
            }
            print(json.dumps(log_entry), flush=True)
            last_log_time = current_time
    
    # Final summary
    final_time = time.time()
    total_elapsed = final_time - measurement_start
    final_summary = {
        "work_unit": "signature",
        "total_count": signatures_verified,
        "measurement_duration_seconds": total_elapsed,
        "signatures_per_second": signatures_verified / total_elapsed if total_elapsed > 0 else 0,
        "algorithm": "ed25519",
        "key_size": 256,
        "measurement_start": measurement_start,
        "measurement_end": final_time
    }
    print(json.dumps({"final": final_summary}), flush=True)

if __name__ == "__main__":
    main()

