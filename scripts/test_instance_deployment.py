#!/usr/bin/env python3
"""Test deployment of each instance type to verify they work."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.benchmarking.provision import provision_instance, terminate_instance

def test_instance_type(instance_type, instance_config, region):
    """Test provisioning a single instance type."""
    print(f"\n{'='*60}")
    print(f"Testing instance type: {instance_type}")
    print(f"{'='*60}")
    
    instance_id = None
    try:
        instance_id, public_ip, private_key = provision_instance(
            instance_type,
            instance_config,
            region=region
        )
        print(f"✓ Successfully provisioned {instance_type}")
        print(f"  Instance ID: {instance_id}")
        print(f"  Public IP: {public_ip}")
        print(f"  Private key available: {private_key is not None}")
        return True
    except Exception as e:
        print(f"✗ Failed to provision {instance_type}")
        print(f"  Error: {e}")
        return False
    finally:
        if instance_id:
            print(f"  Terminating instance {instance_id}...")
            try:
                terminate_instance(instance_id, region=region)
                print(f"  ✓ Instance terminated")
            except Exception as e:
                print(f"  ✗ Error terminating: {e}")

def main():
    config_path = "config/instances.json"
    
    with open(config_path) as f:
        config = json.load(f)
    
    region = config["region"]
    instances = config["instances"]
    
    print(f"Testing instance deployment in region: {region}")
    print(f"Instance types to test: {list(instances.keys())}")
    
    results = {}
    for instance_type, instance_config in instances.items():
        results[instance_type] = test_instance_type(instance_type, instance_config, region)
        # Wait a bit between tests
        import time
        time.sleep(5)
    
    print(f"\n{'='*60}")
    print("DEPLOYMENT TEST SUMMARY")
    print(f"{'='*60}")
    
    for instance_type, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {instance_type}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n✓ All instance types can be deployed successfully!")
    else:
        print("\n✗ Some instance types failed to deploy")
        print("Please fix the errors above before running benchmarks")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

