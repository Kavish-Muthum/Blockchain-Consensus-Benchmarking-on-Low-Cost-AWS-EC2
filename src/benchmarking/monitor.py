#!/usr/bin/env python3
"""
CloudWatch and custom metric collection for benchmarking.
"""
import boto3
import json
import time
import logging
import paramiko
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricCollector:
    """Collects metrics from CloudWatch and custom sources."""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.cloudwatch = boto3.client("cloudwatch", region_name=region)
        self.metrics = []
    
    def collect_cloudwatch_metrics(
        self,
        instance_id: str,
        start_time: datetime,
        end_time: datetime,
        interval_minutes: int = 1
    ) -> List[Dict]:
        """Collect CloudWatch metrics for an instance."""
        metrics_to_collect = [
            "CPUUtilization",
            "NetworkIn",
            "NetworkOut",
            "CPUCreditUsage",
            "CPUCreditBalance",
            "DiskReadOps",
            "DiskWriteOps"
        ]
        
        collected_metrics = []
        
        for metric_name in metrics_to_collect:
            try:
                response = self.cloudwatch.get_metric_statistics(
                    Namespace="AWS/EC2",
                    MetricName=metric_name,
                    Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=interval_minutes * 60,  # Convert to seconds
                    Statistics=["Average", "Maximum"]
                )
                
                if response["Datapoints"]:
                    for datapoint in response["Datapoints"]:
                        collected_metrics.append({
                            "timestamp": datapoint["Timestamp"].isoformat(),
                            "metric": metric_name,
                            "average": datapoint.get("Average"),
                            "maximum": datapoint.get("Maximum"),
                            "unit": datapoint.get("Unit", "None")
                        })
            except ClientError as e:
                logger.warning(f"Could not collect {metric_name}: {e}")
        
        return collected_metrics
    
    def collect_gpu_metrics(
        self,
        hostname: str,
        username: str = "ec2-user",
        key_path: Optional[str] = None,
        private_key: Optional[str] = None,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> List[Dict]:
        """Collect GPU metrics via SSH using nvidia-smi."""
        gpu_metrics = []
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if private_key:
                import io
                from paramiko import RSAKey, Ed25519Key
                key_file = io.StringIO(private_key)
                try:
                    key = RSAKey.from_private_key(key_file)
                except:
                    key_file.seek(0)
                    key = Ed25519Key.from_private_key(key_file)
                ssh.connect(hostname, username=username, pkey=key, timeout=30)
            elif key_path:
                ssh.connect(hostname, username=username, key_filename=key_path, timeout=30)
            else:
                raise ValueError("Either key_path or private_key must be provided")
            
            # Query nvidia-smi
            stdin, stdout, stderr = ssh.exec_command(
                'nvidia-smi --query-gpu=timestamp,name,utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu,power.draw --format=csv,noheader,nounits'
            )
            
            output = stdout.read().decode()
            ssh.close()
            
            # Parse nvidia-smi output
            for line in output.strip().split("\n"):
                if not line:
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 8:
                    gpu_metrics.append({
                        "timestamp": parts[0],
                        "gpu_name": parts[1],
                        "gpu_utilization_percent": float(parts[2]) if parts[2] else 0,
                        "memory_utilization_percent": float(parts[3]) if parts[3] else 0,
                        "memory_used_mb": float(parts[4]) if parts[4] else 0,
                        "memory_total_mb": float(parts[5]) if parts[5] else 0,
                        "temperature_c": float(parts[6]) if parts[6] else 0,
                        "power_draw_watts": float(parts[7]) if parts[7] else 0
                    })
        
        except Exception as e:
            logger.warning(f"Could not collect GPU metrics: {e}")
        
        return gpu_metrics
    
    def collect_fpga_metrics(
        self,
        hostname: str,
        username: str = "ec2-user",
        key_path: Optional[str] = None,
        private_key: Optional[str] = None
    ) -> List[Dict]:
        """Collect FPGA metrics via SSH."""
        fpga_metrics = []
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if private_key:
                import io
                from paramiko import RSAKey, Ed25519Key
                key_file = io.StringIO(private_key)
                try:
                    key = RSAKey.from_private_key(key_file)
                except:
                    key_file.seek(0)
                    key = Ed25519Key.from_private_key(key_file)
                ssh.connect(hostname, username=username, pkey=key, timeout=30)
            elif key_path:
                ssh.connect(hostname, username=username, key_filename=key_path, timeout=30)
            else:
                raise ValueError("Either key_path or private_key must be provided")
            
            # Query FPGA status (Xilinx tools)
            stdin, stdout, stderr = ssh.exec_command("sudo fpga-describe-local-image-slots --json")
            output = stdout.read().decode()
            ssh.close()
            
            if output:
                try:
                    fpga_data = json.loads(output)
                    fpga_metrics.append({
                        "timestamp": datetime.now().isoformat(),
                        "fpga_data": fpga_data
                    })
                except json.JSONDecodeError:
                    logger.warning("Could not parse FPGA metrics JSON")
        
        except Exception as e:
            logger.warning(f"Could not collect FPGA metrics: {e}")
        
        return fpga_metrics
    
    def collect_memory_metrics(
        self,
        hostname: str,
        username: str = "ec2-user",
        key_path: Optional[str] = None,
        private_key: Optional[str] = None
    ) -> Dict:
        """Collect memory metrics via SSH."""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if private_key:
                import io
                from paramiko import RSAKey, Ed25519Key
                key_file = io.StringIO(private_key)
                try:
                    key = RSAKey.from_private_key(key_file)
                except:
                    key_file.seek(0)
                    key = Ed25519Key.from_private_key(key_file)
                ssh.connect(hostname, username=username, pkey=key, timeout=30)
            elif key_path:
                ssh.connect(hostname, username=username, key_filename=key_path, timeout=30)
            else:
                raise ValueError("Either key_path or private_key must be provided")
            
            # Get memory info
            stdin, stdout, stderr = ssh.exec_command("free -m")
            output = stdout.read().decode()
            ssh.close()
            
            # Parse free output
            lines = output.strip().split("\n")
            if len(lines) >= 2:
                mem_line = lines[1].split()
                if len(mem_line) >= 4:
                    total = int(mem_line[1])
                    used = int(mem_line[2])
                    free = int(mem_line[3])
                    return {
                        "total_mb": total,
                        "used_mb": used,
                        "free_mb": free,
                        "usage_percent": (used / total * 100) if total > 0 else 0
                    }
        
        except Exception as e:
            logger.warning(f"Could not collect memory metrics: {e}")
        
        return {}
    
    def estimate_energy(
        self,
        instance_type: str,
        instance_config: Dict,
        cpu_utilization_percent: float,
        duration_seconds: float,
        gpu_power_watts: Optional[float] = None
    ) -> float:
        """
        Estimate energy consumption in Joules.
        Energy = Power × Time
        
        Note: Even at 0% CPU utilization, instances consume base power (idle consumption).
        This ensures energy estimates are non-zero even when CloudWatch metrics are missing.
        """
        # Base power consumption (TDP)
        base_power_watts = instance_config.get("estimated_tdp_watts", 50)
        
        # Minimum base power (idle consumption ~30% of TDP)
        # This accounts for instance running even at 0% CPU utilization
        idle_power_watts = base_power_watts * 0.30
        
        # Active power scales with CPU utilization (remaining 70% of TDP)
        # At 100% CPU: active_power = 0.70 * base_power
        # At 0% CPU: active_power = 0
        active_power_watts = (base_power_watts * 0.70) * (cpu_utilization_percent / 100.0)
        
        # Total power = idle + active
        total_power_watts = idle_power_watts + active_power_watts
        
        # Add GPU power if available
        if gpu_power_watts:
            total_power_watts += gpu_power_watts
        
        # Calculate energy in Joules (Watts × seconds)
        energy_joules = total_power_watts * duration_seconds
        
        return energy_joules
    
    def aggregate_metrics(
        self,
        cloudwatch_metrics: List[Dict],
        gpu_metrics: Optional[List[Dict]] = None,
        fpga_metrics: Optional[List[Dict]] = None,
        memory_metrics: Optional[Dict] = None
    ) -> Dict:
        """Aggregate all collected metrics."""
        aggregated = {
            "cloudwatch": cloudwatch_metrics,
            "gpu": gpu_metrics or [],
            "fpga": fpga_metrics or [],
            "memory": memory_metrics or {}
        }
        
        # Calculate averages
        cpu_values = [m["average"] for m in cloudwatch_metrics if m["metric"] == "CPUUtilization" and m.get("average")]
        if cpu_values:
            aggregated["average_cpu_percent"] = sum(cpu_values) / len(cpu_values)
            aggregated["max_cpu_percent"] = max(cpu_values)
        else:
            aggregated["average_cpu_percent"] = 0
            aggregated["max_cpu_percent"] = 0
        
        if gpu_metrics:
            gpu_utils = [m["gpu_utilization_percent"] for m in gpu_metrics if m.get("gpu_utilization_percent")]
            if gpu_utils:
                aggregated["average_gpu_percent"] = sum(gpu_utils) / len(gpu_utils)
                aggregated["average_gpu_power_watts"] = sum(m["power_draw_watts"] for m in gpu_metrics if m.get("power_draw_watts")) / len(gpu_metrics)
        
        if memory_metrics:
            aggregated["memory_usage_percent"] = memory_metrics.get("usage_percent", 0)
            aggregated["memory_used_mb"] = memory_metrics.get("used_mb", 0)
            aggregated["memory_total_mb"] = memory_metrics.get("total_mb", 0)
        
        return aggregated

if __name__ == "__main__":
    # Test monitoring
    import sys
    from datetime import datetime, timedelta
    
    collector = MetricCollector()
    
    if len(sys.argv) < 2:
        print("Usage: monitor.py <instance_id>")
        sys.exit(1)
    
    instance_id = sys.argv[1]
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=5)
    
    metrics = collector.collect_cloudwatch_metrics(instance_id, start_time, end_time)
    print(json.dumps(metrics, indent=2))

