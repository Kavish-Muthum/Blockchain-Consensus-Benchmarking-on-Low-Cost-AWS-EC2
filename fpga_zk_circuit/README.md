# Hardware-Accelerated ZK-SNARK FPGA Implementation

This directory contains a simplified proof-of-concept for hardware-accelerated ZK-SNARK proof generation on AWS F1 instances.

## Overview

A complete ZK-SNARK FPGA implementation is extremely complex, requiring:
- Elliptic curve cryptography (pairing operations)
- Polynomial interpolation (FFT)
- Multi-precision arithmetic
- Large memory interfaces

This implementation provides a **simplified proof-of-concept** that demonstrates:
1. FPGA circuit design for arithmetic operations
2. AFI compilation process
3. Software-FPGA interface
4. Hardware acceleration framework

## Simplified Approach

Instead of full ZK-SNARK, we'll implement a **simple arithmetic circuit** that:
- Performs modular arithmetic (foundation of ZK circuits)
- Accelerates constraint checking
- Demonstrates FPGA acceleration concepts

This can be extended to full ZK-SNARK later.

## Architecture

```
Software (Python) → FPGA Shell Interface → Custom FPGA Logic → Results
```

