# Algorithm Implementation: ARM vs x86

## Overview

**Important**: All four algorithms run the **exact same Python code** on both ARM and x86 instances. There are no architecture-specific optimizations. The code is portable Python that runs identically on both platforms.

This document explains:
1. How each algorithm works
2. What Python libraries/functions they use
3. How they're deployed and executed
4. Why they run identically on ARM and x86

---

## 1. Proof of Work (PoW) - SHA-256 Mining

### Algorithm Description

**What it does**: Simulates cryptocurrency mining by repeatedly hashing block data with different nonces until finding a hash that starts with a difficulty target.

### Implementation Details

**File**: `src/workloads/pow.py`

**Core Function**:
```python
def mine_block(nonce, block_template, difficulty_target):
    block_data = f"{block_template}{nonce}".encode()
    block_hash = hashlib.sha256(block_data).hexdigest()
    return block_hash, block_hash.startswith(difficulty_target)
```

**Key Components**:
- **Library Used**: Python's built-in `hashlib` module (SHA-256)
- **Work Unit**: Each hash attempt
- **Process**: 
  1. Concatenate block template with nonce
  2. Compute SHA-256 hash
  3. Check if hash starts with difficulty target (e.g., "00000")
  4. Increment nonce and repeat

**How it runs on ARM and x86**:
- ✅ **Identical Code**: Same Python source code
- ✅ **Same Library**: Python's `hashlib` uses OpenSSL under the hood (pre-installed on both AMIs)
- ✅ **CPU-Only**: No GPU/FPGA acceleration
- ✅ **Single-threaded by default**: Sequential nonce increments
- ⚠️ **Performance Difference**: ARM vs x86 may have different performance due to:
  - Different CPU architectures (ARM vs Intel/AMD)
  - OpenSSL optimizations per architecture
  - Cache sizes and memory bandwidth

**Execution Flow**:
```
1. Warmup (30s): Discard results, let CPU warm up
2. Measurement (300s): 
   - Loop: mine_block() → check hash → increment nonce
   - Log progress every 1 second (JSON output)
   - Count total hashes attempted
3. Final Summary: Calculate hashes_per_second
```

---

## 2. Proof of Stake (PoS) - Ed25519 Signature Verification

### Algorithm Description

**What it does**: Simulates Proof of Stake consensus by repeatedly verifying Ed25519 cryptographic signatures (like validators verifying block attestations).

### Implementation Details

**File**: `src/workloads/pos.py`

**Core Functions**:
```python
def generate_test_data(num_pairs=1000):
    # Generate 1000 message/signature pairs once
    for i in range(num_pairs):
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        message = f"TestMessage_{i}_Benchmark_2024".encode()
        signature = private_key.sign(message)
        test_pairs.append({message, signature, public_key})

def verify_signature(message, signature, public_key_bytes):
    public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
    public_key.verify(signature, message)  # Raises exception if invalid
    return True
```

**Key Components**:
- **Library Used**: `cryptography` library (Python package)
- **Algorithm**: Ed25519 (Edwards-curve Digital Signature Algorithm)
- **Work Unit**: Each signature verification
- **Process**:
  1. Pre-generate 1000 message/signature pairs (once at startup)
  2. Loop: Take a pair → verify signature → cycle through pairs
  3. Count successful verifications

**How it runs on ARM and x86**:
- ✅ **Identical Code**: Same Python source code
- ✅ **Same Library**: `cryptography` package uses native crypto libraries
  - ARM: May use ARM cryptographic extensions if available
  - x86: Uses x86-optimized crypto (AES-NI, etc.)
- ✅ **CPU-Only**: Cryptographic operations run on CPU
- ⚠️ **Performance Difference**: Architecture-specific crypto optimizations:
  - ARM: Potential use of ARMv8 crypto extensions
  - x86: Potential use of AES-NI, AVX instructions
  - Both use optimized native code (not pure Python)

**Execution Flow**:
```
1. Generate 1000 test message/signature pairs (once)
2. Warmup (30s): Verify signatures in loop (discard results)
3. Measurement (300s):
   - Loop: verify_signature() → cycle through pairs
   - Log progress every 1 second
   - Count successful verifications
4. Final Summary: Calculate signatures_per_second
```

---

## 3. Byzantine Fault Tolerance (BFT) - PBFT Consensus Simulation

### Algorithm Description

**What it does**: Simulates Practical Byzantine Fault Tolerance (PBFT) consensus protocol - nodes must agree on messages through Prepare and Commit phases.

### Implementation Details

**File**: `src/workloads/bft.py`

**Core Classes**:
```python
class PBFTNode:
    def prepare(self, message_hash, sequence):
        # Prepare phase: node agrees to prepare message
        self.sequence_number = sequence
        self.prepared = True
        return True
    
    def commit(self, message_hash, sequence):
        # Commit phase: node commits message (if prepared)
        if self.prepared and self.sequence_number == sequence:
            self.committed = True
            return True

class PBFTCluster:
    def run_consensus_round(self, message):
        message_hash = hashlib.sha256(message.encode()).hexdigest()
        
        # Phase 1: Prepare - need (2f+1) votes
        prepare_votes = 0
        for node in self.nodes:
            if node.prepare(message_hash, sequence):
                prepare_votes += 1
        
        if prepare_votes < required_votes:
            return False
        
        # Phase 2: Commit - need (2f+1) votes
        commit_votes = 0
        for node in self.nodes:
            if node.commit(message_hash, sequence):
                commit_votes += 1
        
        return commit_votes >= required_votes
```

**Key Components**:
- **Algorithm**: PBFT (Practical Byzantine Fault Tolerance)
- **Simulation**: All nodes run in-memory (no network)
- **Configuration**: 
  - 4 nodes by default
  - Byzantine tolerance: 1 (can tolerate 1 faulty node)
  - Required votes: 2f+1 = 3 (out of 4 nodes)
- **Work Unit**: Each completed consensus round
- **Message Hash**: Uses SHA-256 (via `hashlib`)

**How it runs on ARM and x86**:
- ✅ **Identical Code**: Same Python simulation code
- ✅ **Pure Python Logic**: Consensus state machine logic (no native code)
- ✅ **Hash Operations**: Uses `hashlib` SHA-256 (same as PoW)
- ✅ **In-Memory Simulation**: All nodes are Python objects (no network)
- ⚠️ **Performance Difference**: 
  - Python interpreter performance (ARM vs x86)
  - Memory access patterns
  - Hash computation speed (same as PoW)

**Execution Flow**:
```
1. Create PBFT cluster with 4 nodes
2. Warmup (30s): Run consensus rounds (discard results)
3. Measurement (300s):
   - Loop: create message → run_consensus_round() → check if successful
   - Log progress every 1 second
   - Count completed rounds
4. Final Summary: Calculate rounds_per_second
```

---

## 4. Zero-Knowledge Proofs (ZK) - ZK-SNARK Simulation

### Algorithm Description

**What it does**: Simulates ZK-SNARK proof generation using a simplified arithmetic circuit. In reality, this is a computational simulation of the workload, not a real cryptographic proof.

### Implementation Details

**File**: `src/workloads/zk.py`

**Core Class**:
```python
class SimpleCircuit:
    def prove(self, secret_input, public_output):
        # Simulate circuit evaluation
        proof_work = 0
        for i in range(self.circuit_size):  # Default: 100 iterations
            # Simulate constraint checking (hash operations)
            temp = hashlib.sha256(f"{secret_input}_{i}_{public_output}".encode()).hexdigest()
            proof_work += int(temp[:8], 16)  # Use hash as "work"
        
        # Simulate polynomial evaluation
        additional_work = hashlib.sha256(f"proof_{secret_input}_{public_output}".encode()).hexdigest()
        
        return {"proof": additional_work, "work_done": proof_work}
```

**Key Components**:
- **Algorithm**: Simplified ZK-SNARK simulation
- **Circuit Size**: 100 constraints (default)
- **Work Unit**: Each proof generated
- **Computation**: Multiple SHA-256 hash operations (simulates constraint checking)
- **Note**: This is a **simulation**, not a real ZK-SNARK. Real ZK-SNARKs involve:
  - Elliptic curve operations
  - Polynomial commitments
  - Pairing operations
  - FFT operations

**How it runs on ARM and x86**:
- ✅ **Identical Code**: Same Python simulation code
- ✅ **Hash-Based Simulation**: Uses `hashlib` SHA-256 (simulates constraint evaluation)
- ✅ **CPU-Only**: All computation on CPU
- ⚠️ **Performance Difference**: 
  - Hash computation speed (same as PoW)
  - Loop performance (Python interpreter)
  - Memory allocation for hash results

**Execution Flow**:
```
1. Create SimpleCircuit with circuit_size=100
2. Warmup (30s): Generate proofs (discard results)
3. Measurement (300s):
   - Loop: create secret input → circuit.prove() → count proofs
   - Log progress every 1 second
   - Count proofs generated
4. Final Summary: Calculate proofs_per_second
```

---

## Deployment and Execution Process

### 1. Instance Provisioning

**ARM Instance (t4g.2xlarge)**:
- AMI: Amazon Linux 2023 (ARM64)
- Architecture: `arm64`
- AMI Pattern: `al2023-ami-*-arm64`

**x86 Instance (t3.2xlarge)**:
- AMI: Amazon Linux 2023 (x86_64)
- Architecture: `x86_64`
- AMI Pattern: `al2023-ami-*-x86_64`

### 2. Instance Setup (User Data Script)

Both instances run the **same setup script**:
```bash
#!/bin/bash
# Update system
yum update -y

# Install Python 3 and pip
yum install -y python3 python3-pip git

# Install monitoring tools
pip3 install psutil
```

**Key Points**:
- ✅ Same Python 3 version
- ✅ Same package manager (yum)
- ✅ Same system libraries (OpenSSL, etc.)
- ⚠️ **Different binaries**: ARM64 vs x86_64 binaries (same source, different compilation)

### 3. Workload Deployment

**Process** (via SSH):
1. Create `/tmp/benchmark` directory on instance
2. Upload workload Python file (e.g., `pow.py`)
3. Make it executable (`chmod +x`)
4. Run with arguments:
   ```bash
   python3 pow.py 30 300 "00000" "BlockTemplate_2024_Benchmark_Consensus_Research"
   ```

**Deployment is identical for ARM and x86**:
- ✅ Same file structure
- ✅ Same command
- ✅ Same Python interpreter (different binaries, same interface)

### 4. Workload Execution

**Execution Environment**:
- **Interpreter**: Python 3 (CPython)
  - ARM: Python 3 compiled for ARM64
  - x86: Python 3 compiled for x86_64
- **Standard Library**: Same Python stdlib code
- **Native Libraries**:
  - `hashlib`: Uses OpenSSL (architecture-specific binary)
  - `cryptography`: Uses native crypto libraries (architecture-specific)

**Output Format**:
- JSON logs every 1 second (stdout)
- Progress messages (stderr)
- Final summary (stdout, JSON)

---

## Why Performance May Differ

### Architecture Differences

**ARM (Graviton2/3)**:
- ARMv8 architecture
- Different instruction set
- Potential crypto extensions (ARMv8 crypto extensions)
- Different memory hierarchy
- Different cache sizes

**x86 (Intel/AMD)**:
- x86-64 architecture
- Different instruction set
- Hardware crypto acceleration (AES-NI, etc.)
- Different memory hierarchy
- Different cache sizes

### Performance Factors

**1. Hash Computation (PoW, BFT, ZK)**:
- OpenSSL optimizations differ per architecture
- ARM may have crypto extensions
- x86 has AES-NI (not used for SHA-256, but affects crypto libs)

**2. Signature Verification (PoS)**:
- `cryptography` library uses native code
- May use architecture-specific crypto instructions
- Ed25519 implementations may differ

**3. Python Interpreter**:
- CPython compiled for each architecture
- Same Python bytecode, different machine code
- GIL (Global Interpreter Lock) behavior identical
- Memory management may differ

**4. System Libraries**:
- Different versions of OpenSSL binaries
- Different system optimizations
- Different compiler optimizations

---

## Summary: Identical Code, Different Performance

| Aspect | ARM (t4g.2xlarge) | x86 (t3.2xlarge) | Status |
|--------|-------------------|------------------|--------|
| **Source Code** | ✅ Same | ✅ Same | Identical |
| **Python Code** | ✅ Same | ✅ Same | Identical |
| **Libraries** | ✅ Same packages | ✅ Same packages | Identical |
| **Execution** | ✅ Same commands | ✅ Same commands | Identical |
| **Binaries** | ⚠️ ARM64 | ⚠️ x86_64 | Different |
| **Performance** | ⚠️ Architecture-dependent | ⚠️ Architecture-dependent | May differ |

**Key Takeaway**: 
- ✅ **Code is identical** - same Python source code runs on both
- ⚠️ **Performance may differ** - due to architecture-specific optimizations in:
  - Python interpreter (CPython)
  - OpenSSL (for hashing)
  - Cryptography library (for signatures)
  - System libraries

**This makes the comparison fair**: We're comparing how each architecture handles the same workload, which is exactly what we want for benchmarking!

---

## Example: PoW Execution Flow

```
ARM Instance (t4g.2xlarge):
├── Provision EC2 instance (ARM64 AMI)
├── Run user data script (install Python 3)
├── Deploy pow.py via SSH
├── Execute: python3 pow.py 30 300 "00000" "..."
│   ├── Python 3 (ARM64 binary) loads
│   ├── hashlib imports OpenSSL (ARM64 binary)
│   ├── Loop: hashlib.sha256() → OpenSSL SHA-256 (ARM-optimized)
│   └── Output: JSON logs with hashes_per_second
└── Collect results

x86 Instance (t3.2xlarge):
├── Provision EC2 instance (x86_64 AMI)
├── Run user data script (install Python 3)
├── Deploy pow.py via SSH
├── Execute: python3 pow.py 30 300 "00000" "..."
│   ├── Python 3 (x86_64 binary) loads
│   ├── hashlib imports OpenSSL (x86_64 binary)
│   ├── Loop: hashlib.sha256() → OpenSSL SHA-256 (x86-optimized)
│   └── Output: JSON logs with hashes_per_second
└── Collect results
```

**Same code, different binaries, potentially different performance!**

