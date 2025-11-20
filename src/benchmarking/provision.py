#!/usr/bin/env python3
"""
EC2 instance provisioning with IAM role support.
"""
import boto3
import json
import time
import logging
import threading
from pathlib import Path
from typing import Dict, Optional, Tuple
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_latest_ami(ec2_client, ami_name_pattern, owner, architecture):
    """Find the latest AMI matching the pattern."""
    try:
        filters = [
            {"Name": "name", "Values": [ami_name_pattern]},
            {"Name": "architecture", "Values": [architecture]},
            {"Name": "state", "Values": ["available"]}
        ]
        if owner:
            filters.append({"Name": "owner-id", "Values": [owner]})
        
        response = ec2_client.describe_images(Filters=filters, Owners=[owner] if owner != "amazon" else ["amazon"])
        
        if not response["Images"]:
            # Fallback to Amazon Linux 2023
            logger.warning(f"AMI not found with pattern {ami_name_pattern}, using Amazon Linux 2023")
            filters = [
                {"Name": "name", "Values": ["al2023-ami-*-*"]},
                {"Name": "architecture", "Values": [architecture]},
                {"Name": "state", "Values": ["available"]}
            ]
            response = ec2_client.describe_images(Filters=filters, Owners=["amazon"])
        
        if not response["Images"]:
            raise ValueError(f"No AMI found for {architecture} architecture")
        
        # Sort by creation date, get latest
        images = sorted(response["Images"], key=lambda x: x["CreationDate"], reverse=True)
        return images[0]["ImageId"]
    except Exception as e:
        logger.error(f"Error finding AMI: {e}")
        raise

def create_security_group(ec2_client, vpc_id, group_name):
    """Create security group for SSH access."""
    try:
        # Check if security group already exists
        response = ec2_client.describe_security_groups(
            Filters=[{"Name": "group-name", "Values": [group_name]}]
        )
        if response["SecurityGroups"]:
            return response["SecurityGroups"][0]["GroupId"]
        
        # Create new security group
        response = ec2_client.create_security_group(
            GroupName=group_name,
            Description="Security group for blockchain benchmarking",
            VpcId=vpc_id
        )
        group_id = response["GroupId"]
        
        # Add SSH rule
        ec2_client.authorize_security_group_ingress(
            GroupId=group_id,
            IpPermissions=[
                {
                    "IpProtocol": "tcp",
                    "FromPort": 22,
                    "ToPort": 22,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "SSH access"}]
                }
            ]
        )
        return group_id
    except ClientError as e:
        if e.response["Error"]["Code"] == "InvalidGroup.Duplicate":
            # Group exists, get its ID
            response = ec2_client.describe_security_groups(
                Filters=[{"Name": "group-name", "Values": [group_name]}]
            )
            return response["SecurityGroups"][0]["GroupId"]
        raise

def get_default_vpc(ec2_client):
    """Get default VPC ID."""
    response = ec2_client.describe_vpcs(
        Filters=[{"Name": "isDefault", "Values": ["true"]}]
    )
    if response["Vpcs"]:
        return response["Vpcs"][0]["VpcId"]
    raise ValueError("No default VPC found")

# Global lock for key pair creation (to prevent race conditions)
_key_pair_lock = threading.Lock()

def create_key_pair(ec2_client, key_name, key_file_path=None):
    """Create or retrieve EC2 key pair."""
    import os
    from pathlib import Path
    import threading
    
    # Default key file path
    if key_file_path is None:
        key_file_path = Path.home() / ".ssh" / f"{key_name}.pem"
    
    key_file_path = Path(key_file_path)
    
    # Use lock to prevent race conditions when multiple threads create key pairs
    with _key_pair_lock:
        # Check again after acquiring lock (another thread might have created it)
        if key_file_path.exists():
            logger.info(f"Using existing key file: {key_file_path}")
            with open(key_file_path, "r") as f:
                return f.read()
        
        try:
            # Check if key pair exists in AWS
            response = ec2_client.describe_key_pairs(
                Filters=[{"Name": "key-name", "Values": [key_name]}]
            )
            if response["KeyPairs"]:
                logger.warning(f"Key pair {key_name} exists in AWS but key file not found locally.")
                logger.warning(f"Deleting existing key pair and creating new one to save private key...")
                # Delete existing key pair so we can recreate and save the private key
                try:
                    ec2_client.delete_key_pair(KeyName=key_name)
                    time.sleep(2)  # Wait for deletion to complete
                except ClientError as e:
                    logger.warning(f"Could not delete existing key pair: {e}")
            
            # Create new key pair
            response = ec2_client.create_key_pair(KeyName=key_name)
            private_key = response["KeyMaterial"]
            
            # Save private key to file
            key_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file_path, "w") as f:
                f.write(private_key)
            # Set secure permissions
            os.chmod(key_file_path, 0o600)
            logger.info(f"Created key pair {key_name} and saved private key to: {key_file_path}")
            
            return private_key
        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidKeyPair.Duplicate":
                # Key pair was created by another thread - check if file exists now
                time.sleep(1)
                if key_file_path.exists():
                    logger.info(f"Key file created by another thread, using: {key_file_path}")
                    with open(key_file_path, "r") as f:
                        return f.read()
                logger.error(f"Key pair {key_name} already exists but we couldn't delete it.")
                logger.error("Please manually delete the key pair or provide the key file.")
                raise ValueError(f"Key pair {key_name} exists but private key not available. Please delete the AWS key pair or provide key file at {key_file_path}.")
            raise

def generate_user_data(instance_type):
    """Generate user data script for instance setup."""
    user_data = f"""#!/bin/bash
# Update system
yum update -y

# Install Python 3 and pip
yum install -y python3 python3-pip git

# Install monitoring tools
pip3 install psutil

# For GPU instances, install NVIDIA drivers and GPU libraries
if [[ "{instance_type}" == g4dn* ]]; then
    echo "GPU instance detected - setting up GPU acceleration..."
    # NVIDIA drivers should be pre-installed on Deep Learning AMI
    # Install GPU Python libraries
    pip3 install pycuda cupy-cuda11x --quiet || echo "GPU libraries installation failed (may need CUDA setup)"
    echo "GPU setup complete"
fi

# For FPGA instances
if [[ "{instance_type}" == f1* ]]; then
    # FPGA Developer AMI should have tools pre-installed
    echo "FPGA instance detected - setting up Cloud-ZK..."
    
    # Install Rust (required for Cloud-ZK)
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source $HOME/.cargo/env
    
    # Clone Cloud-ZK repository
    cd /tmp
    if [ ! -d "cloud-zk" ]; then
        git clone https://github.com/supranational/cloud-zk.git || echo "Failed to clone Cloud-ZK"
    fi
    
    # Note: AFI loading must be done manually or via separate script
    # AFI ID should be provided via environment variable or instance tags
    echo "Cloud-ZK setup initiated. Load AFI manually or via script."
fi

# Wait for system to be ready
sleep 30
"""
    return user_data

def provision_instance(
    instance_type: str,
    instance_config: Dict,
    region: str = "us-east-1",
    key_name: str = "blockchain-benchmark-key",
    security_group_name: str = "blockchain-benchmark-sg",
    iam_role_name: Optional[str] = None,
    key_file_path: Optional[str] = None
) -> Tuple[str, str, Optional[str]]:
    """
    Provision an EC2 instance.
    Returns: (instance_id, public_ip, private_key)
    """
    ec2_client = boto3.client("ec2", region_name=region)
    
    try:
        # Get default VPC
        vpc_id = get_default_vpc(ec2_client)
        logger.info(f"Using VPC: {vpc_id}")
        
        # Create security group
        sg_id = create_security_group(ec2_client, vpc_id, security_group_name)
        logger.info(f"Security group: {sg_id}")
        
        # Create or get key pair
        if key_file_path is None:
            key_file_path = str(Path.home() / ".ssh" / f"{key_name}.pem")
        
        key_file = Path(key_file_path)
        
        # If key file exists locally, use it
        if key_file.exists():
            logger.info(f"Using existing key file: {key_file_path}")
            with open(key_file, "r") as f:
                private_key = f.read()
        else:
            # Try to create or retrieve key pair
            try:
                private_key = create_key_pair(ec2_client, key_name, key_file_path)
                logger.info(f"Key pair ready: {key_name}")
            except ValueError as e:
                logger.error(str(e))
                raise
        
        # Get AMI
        ami_id = get_latest_ami(
            ec2_client,
            instance_config.get("ami_name_pattern", "al2023-ami-*-*"),
            instance_config.get("ami_owner", "amazon"),
            instance_config.get("architecture", "x86_64")
        )
        logger.info(f"Using AMI: {ami_id}")
        
        # Prepare IAM instance profile if role is specified
        iam_instance_profile = None
        if iam_role_name:
            iam_client = boto3.client("iam", region_name=region)
            try:
                # Check if instance profile exists
                profiles = iam_client.list_instance_profiles_for_role(RoleName=iam_role_name)
                if profiles["InstanceProfiles"]:
                    iam_instance_profile = {"Name": profiles["InstanceProfiles"][0]["InstanceProfileName"]}
                else:
                    logger.warning(f"IAM role {iam_role_name} found but no instance profile. Creating one...")
                    # Create instance profile
                    profile_name = f"{iam_role_name}-profile"
                    iam_client.create_instance_profile(InstanceProfileName=profile_name)
                    iam_client.add_role_to_instance_profile(
                        InstanceProfileName=profile_name,
                        RoleName=iam_role_name
                    )
                    time.sleep(5)  # Wait for propagation
                    iam_instance_profile = {"Name": profile_name}
            except ClientError as e:
                logger.warning(f"Could not set up IAM instance profile: {e}")
        
        # Generate user data
        user_data = generate_user_data(instance_type)
        
        # Launch instance
        launch_kwargs = {
            "ImageId": ami_id,
            "InstanceType": instance_type,
            "MinCount": 1,
            "MaxCount": 1,
            "SecurityGroupIds": [sg_id],
            "KeyName": key_name,
            "UserData": user_data,
            "TagSpecifications": [
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Name", "Value": f"blockchain-benchmark-{instance_type}"},
                        {"Key": "Project", "Value": "blockchain-benchmarking"}
                    ]
                }
            ]
        }
        
        if iam_instance_profile:
            launch_kwargs["IamInstanceProfile"] = iam_instance_profile
        
        logger.info(f"Launching instance {instance_type}...")
        response = ec2_client.run_instances(**launch_kwargs)
        
        instance_id = response["Instances"][0]["InstanceId"]
        logger.info(f"Instance launched: {instance_id}")
        
        # Wait for instance to be running
        waiter = ec2_client.get_waiter("instance_running")
        waiter.wait(InstanceIds=[instance_id])
        logger.info(f"Instance {instance_id} is running")
        
        # Get public IP
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        instance = response["Reservations"][0]["Instances"][0]
        public_ip = instance.get("PublicIpAddress")
        
        if not public_ip:
            # Try getting public DNS name
            public_ip = instance.get("PublicDnsName")
        
        logger.info(f"Instance {instance_id} public IP: {public_ip}")
        
        # Wait for SSH to be ready (check system status)
        logger.info("Waiting for instance to be ready...")
        time.sleep(60)  # Wait for user data script to complete
        
        return instance_id, public_ip, private_key
        
    except Exception as e:
        logger.error(f"Error provisioning instance: {e}")
        raise

def terminate_instance(instance_id: str, region: str = "us-east-1"):
    """Terminate an EC2 instance."""
    ec2_client = boto3.client("ec2", region_name=region)
    try:
        ec2_client.terminate_instances(InstanceIds=[instance_id])
        logger.info(f"Terminated instance: {instance_id}")
        
        # Wait for termination
        waiter = ec2_client.get_waiter("instance_terminated")
        waiter.wait(InstanceIds=[instance_id])
    except Exception as e:
        logger.error(f"Error terminating instance {instance_id}: {e}")
        raise

if __name__ == "__main__":
    # Test provisioning
    import sys
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config/instances.json"
    
    with open(config_path) as f:
        config = json.load(f)
    
    instance_type = sys.argv[2] if len(sys.argv) > 2 else "t3.micro"
    instance_config = config["instances"][instance_type]
    
    instance_id, public_ip, private_key = provision_instance(
        instance_type,
        instance_config,
        region=config["region"]
    )
    
    print(f"Instance ID: {instance_id}")
    print(f"Public IP: {public_ip}")

