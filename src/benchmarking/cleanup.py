#!/usr/bin/env python3
"""
Cleanup script to terminate all benchmark instances.
"""
import boto3
import json
import logging
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_benchmark_instances(region: str = "us-east-1") -> List[str]:
    """Find all instances tagged for benchmarking."""
    ec2_client = boto3.client("ec2", region_name=region)
    
    try:
        response = ec2_client.describe_instances(
            Filters=[
                {"Name": "tag:Project", "Values": ["blockchain-benchmarking"]},
                {"Name": "instance-state-name", "Values": ["running", "pending", "stopping", "stopped"]}
            ]
        )
        
        instance_ids = []
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                instance_ids.append(instance["InstanceId"])
        
        return instance_ids
    except Exception as e:
        logger.error(f"Error finding instances: {e}")
        return []

def terminate_all_instances(region: str = "us-east-1"):
    """Terminate all benchmark instances."""
    ec2_client = boto3.client("ec2", region_name=region)
    
    instance_ids = find_benchmark_instances(region)
    
    if not instance_ids:
        logger.info("No benchmark instances found")
        return
    
    logger.info(f"Found {len(instance_ids)} instances to terminate: {instance_ids}")
    
    try:
        ec2_client.terminate_instances(InstanceIds=instance_ids)
        logger.info(f"Terminated {len(instance_ids)} instances")
        
        # Wait for termination
        waiter = ec2_client.get_waiter("instance_terminated")
        waiter.wait(InstanceIds=instance_ids)
        logger.info("All instances terminated")
    except Exception as e:
        logger.error(f"Error terminating instances: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Cleanup benchmark instances")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--config", default="config/instances.json", help="Instance config path")
    
    args = parser.parse_args()
    
    # Get region from config if available
    try:
        with open(args.config) as f:
            config = json.load(f)
            region = config.get("region", args.region)
    except:
        region = args.region
    
    terminate_all_instances(region)

