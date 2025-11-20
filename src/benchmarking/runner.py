#!/usr/bin/env python3
"""
Main benchmark orchestrator that runs workloads, collects metrics, and saves raw logs.
"""
import json
import os
import sys
import time
import logging
import paramiko
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from provision import provision_instance, terminate_instance
from monitor import MetricCollector

# Configure logging to write to both console and file
def setup_logging(results_dir: str):
    """Set up logging to both console and a progress log file."""
    log_dir = Path(results_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "benchmark_progress.log"
    
    # Create formatters
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # File handler
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    return log_file

logger = logging.getLogger(__name__)

class BenchmarkRunner:
    """Runs benchmarks on EC2 instances."""
    
    def __init__(self, config_path: str = "config/instances.json", workload_config_path: str = "config/workloads.json", results_dir: str = "results"):
        with open(config_path) as f:
            self.instance_config = json.load(f)
        with open(workload_config_path) as f:
            self.workload_config = json.load(f)
        
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        (self.results_dir / "raw_logs").mkdir(exist_ok=True)
        
        # Set up logging to file and console
        self.log_file = setup_logging(str(self.results_dir))
        logger.info(f"Progress log available at: {self.log_file}")
        logger.info(f"Monitor progress in another terminal with: tail -f {self.log_file}")
        
        self.metric_collector = MetricCollector(region=self.instance_config["region"])
        self.active_instances = {}  # instance_type -> (instance_id, public_ip, private_key)
        self.benchmark_counter = 0
        self.total_benchmarks = 0
        
    def deploy_workload(self, hostname: str, workload_name: str, workload_path: str, 
                       username: str = "ec2-user", key_path: Optional[str] = None, 
                       private_key: Optional[str] = None) -> bool:
        """Deploy workload script to instance via SSH."""
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
                ssh.connect(hostname, username=username, pkey=key, timeout=60)
            elif key_path:
                ssh.connect(hostname, username=username, key_filename=key_path, timeout=60)
            else:
                raise ValueError("Either key_path or private_key must be provided")
            
            # Create benchmark directory
            stdin, stdout, stderr = ssh.exec_command("mkdir -p /tmp/benchmark")
            stdout.channel.recv_exit_status()
            
            # Upload workload script
            sftp = ssh.open_sftp()
            remote_path = f"/tmp/benchmark/{workload_name}.py"
            sftp.put(workload_path, remote_path)
            sftp.chmod(remote_path, 0o755)
            sftp.close()
            
            # Install Python dependencies if needed
            workload_deps = {
                "pos": "cryptography",
                "pow": "",
                "bft": "",
                "zk": ""
            }
            if workload_name in workload_deps and workload_deps[workload_name]:
                stdin, stdout, stderr = ssh.exec_command(f"pip3 install {workload_deps[workload_name]}")
                stdout.channel.recv_exit_status()
            
            ssh.close()
            return True
        
        except Exception as e:
            logger.error(f"Error deploying workload to {hostname}: {e}")
            return False
    
    def run_workload(self, hostname: str, workload_name: str, workload_args: List[str],
                    username: str = "ec2-user", key_path: Optional[str] = None, 
                    private_key: Optional[str] = None, verbose: bool = True) -> Tuple[str, int]:
        """Run workload on instance via SSH and collect output."""
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
                ssh.connect(hostname, username=username, pkey=key, timeout=60)
            elif key_path:
                ssh.connect(hostname, username=username, key_filename=key_path, timeout=60)
            else:
                raise ValueError("Either key_path or private_key must be provided")
            
            # Run workload
            cmd = f"cd /tmp/benchmark && python3 {workload_name}.py {' '.join(workload_args)}"
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=600)
            
            # Collect output and log progress in real-time
            output = ""
            exit_code = None
            
            # Read output line by line and log progress in real-time
            logger.info(f"  >>> Executing command on instance: {cmd}")
            logger.info(f"  >>> Waiting for output from {hostname}...")
            
            while True:
                line = stdout.readline()
                if not line:
                    break
                output += line
                
                # Print all output to console in real-time
                if verbose:
                    print(line.rstrip(), flush=True)
                
                # Log progress updates in real-time
                line_stripped = line.strip()
                if line_stripped:
                    try:
                        data = json.loads(line_stripped)
                        if "work_unit" in data and "count" in data and "elapsed_seconds" in data:
                            work_unit = data.get("work_unit", "work")
                            count = data.get("count", 0)
                            elapsed = data.get("elapsed_seconds", 0)
                            rate_key = f"{work_unit}s_per_second" if work_unit.endswith("s") else f"{work_unit}s_per_second"
                            rate = data.get(rate_key, data.get("hashes_per_second", data.get("signatures_per_second", 
                                     data.get("rounds_per_second", data.get("proofs_per_second", 0)))))
                            logger.info(f"  >>> Progress: {count:,} {work_unit}s in {elapsed:.1f}s ({rate:.2f} {work_unit}s/sec)")
                    except json.JSONDecodeError:
                        # Not JSON, might be stderr message
                        if any(keyword in line_stripped for keyword in ["MEASUREMENT:", "WARMUP:", "GENERATING:", "GENERATED:", "SINGLE-THREADED:"]):
                            logger.info(f"  >>> {line_stripped}")
                            if verbose:
                                print(f"  >>> {line_stripped}", flush=True)
            
            # Wait for command to complete
            exit_code = stdout.channel.recv_exit_status()
            
            # Also get stderr
            stderr_output = ""
            while True:
                line = stderr.readline()
                if not line:
                    break
                stderr_output += line
            
            ssh.close()
            
            return output, exit_code
        
        except Exception as e:
            logger.error(f"Error running workload on {hostname}: {e}")
            return "", -1
    
    def collect_metrics_async(self, instance_id: str, instance_type: str, 
                             instance_config: Dict, start_time: datetime,
                             hostname: Optional[str] = None, private_key: Optional[str] = None):
        """Collect metrics asynchronously during benchmark."""
        def collect():
            end_time = start_time + timedelta(seconds=self.workload_config["measurement_seconds"] + 60)
            time.sleep(60)  # Wait for metrics to be available in CloudWatch
            
            # Collect CloudWatch metrics
            cloudwatch_metrics = self.metric_collector.collect_cloudwatch_metrics(
                instance_id, start_time, end_time, interval_minutes=1
            )
            
            # Collect custom metrics
            gpu_metrics = None
            fpga_metrics = None
            memory_metrics = None
            
            if instance_type.startswith("g4dn") and hostname:
                gpu_metrics = self.metric_collector.collect_gpu_metrics(
                    hostname, private_key=private_key
                )
            
            if instance_type.startswith("f1") and hostname:
                fpga_metrics = self.metric_collector.collect_fpga_metrics(
                    hostname, private_key=private_key
                )
            
            if hostname:
                memory_metrics = self.metric_collector.collect_memory_metrics(
                    hostname, private_key=private_key
                )
            
            # Store metrics
            self.collected_metrics[instance_type] = self.metric_collector.aggregate_metrics(
                cloudwatch_metrics, gpu_metrics, fpga_metrics, memory_metrics
            )
        
        thread = threading.Thread(target=collect)
        thread.daemon = True
        thread.start()
        return thread
    
    def run_benchmark(self, instance_type: str, workload_name: str, 
                     iam_role_name: Optional[str] = None) -> Dict:
        """Run a single benchmark: (instance_type, workload) combination."""
        self.benchmark_counter += 1
        progress_msg = f"[{self.benchmark_counter}/{self.total_benchmarks}]"
        logger.info(f"{progress_msg} Starting benchmark: {instance_type} / {workload_name}")
        
        # Get instance and workload configs
        instance_config = self.instance_config["instances"][instance_type]
        workload_cfg = self.workload_config["workloads"][workload_name]
        
        instance_id = None
        public_ip = None
        private_key = None
        
        try:
            # Provision instance
            logger.info(f"Provisioning {instance_type}...")
            instance_id, public_ip, private_key = provision_instance(
                instance_type,
                instance_config,
                region=self.instance_config["region"],
                iam_role_name=iam_role_name
            )
            
            self.active_instances[instance_type] = (instance_id, public_ip, private_key)
            
            # Wait for instance to be ready
            logger.info(f"Waiting for instance {instance_id} to stabilize...")
            time.sleep(60)
            
            # Deploy workload
            workload_path = Path(f"src/workloads/{workload_name}.py")
            if not workload_path.exists():
                raise FileNotFoundError(f"Workload file not found: {workload_path}")
            
            logger.info(f"Deploying workload {workload_name} to {public_ip}...")
            if not self.deploy_workload(public_ip, workload_name, str(workload_path), private_key=private_key):
                raise RuntimeError(f"Failed to deploy workload {workload_name}")
            
            # Prepare workload arguments
            warmup = self.workload_config["warmup_seconds"]
            measurement = self.workload_config["measurement_seconds"]
            
            if workload_name == "pow":
                workload_args = [str(warmup), str(measurement), workload_cfg["difficulty_target"], workload_cfg["block_template"]]
            elif workload_name == "pos":
                workload_args = [str(warmup), str(measurement)]
            elif workload_name == "bft":
                workload_args = [str(warmup), str(measurement), str(workload_cfg["node_count"]), 
                               str(workload_cfg["byzantine_tolerance"]), str(workload_cfg["message_size_bytes"])]
            elif workload_name == "zk":
                workload_args = [str(warmup), str(measurement), str(workload_cfg["circuit_size"]), str(workload_cfg["input_size"])]
            else:
                workload_args = [str(warmup), str(measurement)]
            
            # Initialize metrics collection
            self.collected_metrics = {}
            measurement_start = datetime.utcnow()
            
            # Start metric collection
            logger.info("Starting metric collection...")
            metric_thread = self.collect_metrics_async(
                instance_id, instance_type, instance_config, measurement_start, public_ip, private_key
            )
            
            # Auto-select optimized workload (same logic as in run_benchmark_on_provisioned_instance)
            optimized_workload = workload_name
            if instance_type.startswith("g4dn") and workload_name == "pow":
                gpu_workload_path = Path(f"src/workloads/{workload_name}_gpu.py")
                if gpu_workload_path.exists():
                    optimized_workload = f"{workload_name}_gpu"
            elif instance_type.startswith("f1") and workload_name == "zk":
                fpga_workload_path = Path(f"src/workloads/{workload_name}_cloudzk.py")
                if fpga_workload_path.exists():
                    optimized_workload = f"{workload_name}_cloudzk"
            
            # Run workload with verbose output
            logger.info("=" * 70)
            logger.info(f"RUNNING TEST: {instance_type} / {workload_name}")
            logger.info(f"  Instance: {instance_id} ({public_ip})")
            logger.info(f"  Workload: {optimized_workload} with args: {workload_args}")
            logger.info(f"  Duration: {measurement}s measurement (warmup: {warmup}s)")
            logger.info(f"  Status: Workload will output progress to console in real-time...")
            logger.info("=" * 70)
            
            output, exit_code = self.run_workload(
                public_ip, optimized_workload, workload_args, private_key=private_key, verbose=True
            )
            
            # Print workload output summary
            if output:
                logger.info("=" * 70)
                logger.info(f"WORKLOAD OUTPUT SUMMARY ({instance_type} / {workload_name}):")
                logger.info("-" * 70)
                # Show final summary from workload
                for line in output.split("\n"):
                    if line.strip() and ("final" in line.lower() or "total" in line.lower()):
                        try:
                            data = json.loads(line)
                            if "final" in data:
                                final = data["final"]
                                logger.info(f"  Final Count: {final.get('total_count', 'N/A')}")
                                logger.info(f"  Duration: {final.get('measurement_duration_seconds', 'N/A'):.1f}s")
                                rate_key = next((k for k in final.keys() if "per_second" in k), None)
                                if rate_key:
                                    logger.info(f"  Throughput: {final.get(rate_key, 'N/A'):.2f} {rate_key.replace('_per_second', '')}/sec")
                        except:
                            if "final" in line.lower() or "total" in line.lower():
                                logger.info(f"  {line}")
                logger.info("-" * 70)
            
            # Print workload output to console
            if output:
                logger.info("=" * 70)
                logger.info(f"WORKLOAD OUTPUT ({instance_type} / {workload_name}):")
                logger.info("-" * 70)
                for line in output.split("\n"):
                    if line.strip():
                        logger.info(f"  {line}")
                logger.info("-" * 70)
            
            if exit_code != 0:
                logger.warning(f"Workload exited with code {exit_code}")
            
            # Wait for metrics collection to complete
            metric_thread.join(timeout=120)
            
            # Parse workload output
            workload_data = self.parse_workload_output(output, workload_name)
            
            # Get collected metrics
            metrics = self.collected_metrics.get(instance_type, {})
            
            # Calculate energy
            cpu_util = metrics.get("average_cpu_percent", 0)
            duration = self.workload_config["measurement_seconds"]
            gpu_power = metrics.get("average_gpu_power_watts")
            
            energy_joules = self.metric_collector.estimate_energy(
                instance_type, instance_config, cpu_util, duration, gpu_power
            )
            
            # Prepare results
            result = {
                "instance_type": instance_type,
                "workload": workload_name,
                "instance_id": instance_id,
                "public_ip": public_ip,
                "measurement_start": measurement_start.isoformat(),
                "measurement_duration_seconds": duration,
                "workload_output": workload_data,
                "metrics": metrics,
                "energy_joules": energy_joules,
                "work_units_completed": workload_data.get("total_count", 0),
                "throughput_work_per_sec": workload_data.get("total_count", 0) / duration if duration > 0 else 0,
                "efficiency_joules_per_work": energy_joules / workload_data.get("total_count", 1) if workload_data.get("total_count", 0) > 0 else float('inf'),
                "instance_config": instance_config
            }
            
            # Save raw logs
            log_file = self.results_dir / "raw_logs" / f"{instance_type}_{workload_name}.json"
            with open(log_file, "w") as f:
                json.dump(result, f, indent=2)
            
            progress_msg = f"[{self.benchmark_counter}/{self.total_benchmarks}]"
            logger.info(f"{progress_msg} ✓ Benchmark completed: {instance_type} / {workload_name}")
            logger.info(f"{progress_msg}   Work units: {workload_data.get('total_count', 0)}")
            logger.info(f"{progress_msg}   Throughput: {result['throughput_work_per_sec']:.2f} work/sec")
            logger.info(f"{progress_msg}   Energy: {energy_joules:.2f} Joules")
            
            return result
        
        except Exception as e:
            logger.error(f"Error running benchmark {instance_type} / {workload_name}: {e}")
            raise
        
        finally:
            # Clean up instance
            if instance_id:
                logger.info(f"Terminating instance {instance_id}...")
                try:
                    terminate_instance(instance_id, region=self.instance_config["region"])
                    if instance_type in self.active_instances:
                        del self.active_instances[instance_type]
                except Exception as e:
                    logger.error(f"Error terminating instance {instance_id}: {e}")
    
    def parse_workload_output(self, output: str, workload_name: str) -> Dict:
        """Parse workload output to extract work units."""
        workload_data = {}
        
        # Parse JSON lines from output
        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                if "final" in data:
                    workload_data = data["final"]
                    break
                elif "work_unit" in data:
                    # Update with latest progress
                    workload_data.update(data)
            except json.JSONDecodeError:
                continue
        
        return workload_data
    
    def run_workloads_on_instance(self, instance_type: str, workloads: List[str], 
                                  iam_role_name: Optional[str] = None) -> List[Dict]:
        """Run all workloads sequentially on a single instance."""
        results = []
        instance_id = None
        public_ip = None
        private_key = None
        
        try:
            # Provision instance once
            logger.info(f"--- Provisioning {instance_type} ---")
            instance_config = self.instance_config["instances"][instance_type]
            instance_id, public_ip, private_key = provision_instance(
                instance_type,
                instance_config,
                region=self.instance_config["region"],
                iam_role_name=iam_role_name
            )
            
            self.active_instances[instance_type] = (instance_id, public_ip, private_key)
            logger.info(f"✓ Instance {instance_type} ({instance_id}) ready at {public_ip}")
            
            # Wait for instance to be ready
            logger.info(f"Waiting for instance {instance_id} to stabilize (60s)...")
            time.sleep(60)
            logger.info(f"Instance {instance_id} stabilized")
            
            # Run each workload sequentially on this instance
            for idx, workload_name in enumerate(workloads, 1):
                try:
                    logger.info(f"--- [{idx}/{len(workloads)}] Running {workload_name} on {instance_type} ---")
                    result = self.run_benchmark_on_provisioned_instance(
                        instance_type, workload_name, instance_id, public_ip, private_key, instance_config
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed benchmark {instance_type} / {workload_name}: {e}")
                    self.benchmark_counter += 1  # Count failed benchmarks
                    continue
        
        except Exception as e:
            logger.error(f"Error provisioning or running benchmarks on {instance_type}: {e}")
        
        finally:
            # Clean up instance after all workloads
            if instance_id:
                logger.info(f"--- Terminating instance {instance_type} ({instance_id}) ---")
                try:
                    terminate_instance(instance_id, region=self.instance_config["region"])
                    if instance_type in self.active_instances:
                        del self.active_instances[instance_type]
                    logger.info(f"✓ Instance {instance_id} terminated")
                except Exception as e:
                    logger.error(f"Error terminating instance {instance_id}: {e}")
        
        return results
    
    def run_benchmark_on_provisioned_instance(self, instance_type: str, workload_name: str,
                                             instance_id: str, public_ip: str, private_key: str,
                                             instance_config: Dict) -> Dict:
        """Run a single benchmark on an already-provisioned instance."""
        self.benchmark_counter += 1
        progress_msg = f"[{self.benchmark_counter}/{self.total_benchmarks}]"
        logger.info(f"{progress_msg} Starting benchmark: {instance_type} / {workload_name}")
        
        workload_cfg = self.workload_config["workloads"][workload_name]
        
        # Prepare workload arguments
        warmup = self.workload_config["warmup_seconds"]
        measurement = self.workload_config["measurement_seconds"]
        
        # Auto-select optimized workload version based on instance type
        # GPU instances: use GPU-optimized workloads if available
        # FPGA instances: use FPGA-optimized workloads if available
        optimized_workload = workload_name
        if instance_type.startswith("g4dn") and workload_name == "pow":
            # Try GPU version for PoW on GPU instances
            gpu_workload_path = Path(f"src/workloads/{workload_name}_gpu.py")
            if gpu_workload_path.exists():
                optimized_workload = f"{workload_name}_gpu"
                logger.info(f"Using GPU-optimized workload: {optimized_workload}")
        elif instance_type.startswith("f1") and workload_name == "zk":
            # Try Cloud-ZK version for ZK on FPGA instances
            fpga_workload_path = Path(f"src/workloads/{workload_name}_cloudzk.py")
            if fpga_workload_path.exists():
                optimized_workload = f"{workload_name}_cloudzk"
                logger.info(f"Using FPGA-optimized workload: {optimized_workload}")
        
        # Get workload configuration (use original or optimized)
        if optimized_workload != workload_name:
            workload_cfg = self.workload_config["workloads"].get(
                optimized_workload, 
                self.workload_config["workloads"].get(workload_name, {})
            )
        
        if optimized_workload == "pow" or optimized_workload == "pow_gpu":
            workload_args = [str(warmup), str(measurement), workload_cfg.get("difficulty_target", "00000"), workload_cfg.get("block_template", "BlockTemplate_2024_Benchmark_Consensus_Research")]
        elif workload_name == "pos":
            workload_args = [str(warmup), str(measurement)]
        elif workload_name == "bft":
            workload_args = [str(warmup), str(measurement), str(workload_cfg.get("node_count", 4)), 
                           str(workload_cfg.get("byzantine_tolerance", 1)), str(workload_cfg.get("message_size_bytes", 1024))]
        elif optimized_workload == "zk" or optimized_workload == "zk_cloudzk":
            workload_args = [str(warmup), str(measurement), str(workload_cfg.get("circuit_size", 100)), str(workload_cfg.get("input_size", 32))]
        else:
            workload_args = [str(warmup), str(measurement)]
        
        # Deploy workload (use optimized version if available)
        workload_path = Path(f"src/workloads/{optimized_workload}.py")
        if not workload_path.exists():
            # Fallback to standard version
            workload_path = Path(f"src/workloads/{workload_name}.py")
            optimized_workload = workload_name
            logger.warning(f"Optimized workload not found, using standard: {workload_name}")
        
        if not workload_path.exists():
            raise FileNotFoundError(f"Workload file not found: {workload_path}")
        
        logger.info(f"{progress_msg} Deploying workload {optimized_workload} to {public_ip}...")
        if not self.deploy_workload(public_ip, optimized_workload, str(workload_path), private_key=private_key):
            raise RuntimeError(f"Failed to deploy workload {optimized_workload}")
        
        # Initialize metrics collection
        self.collected_metrics = {}
        measurement_start = datetime.utcnow()
        
        # Start metric collection
        logger.info(f"{progress_msg} Starting metric collection...")
        metric_thread = self.collect_metrics_async(
            instance_id, instance_type, instance_config, measurement_start, public_ip, private_key
        )
        
        # Run workload with progress updates
        logger.info(f"{progress_msg} Running workload {optimized_workload} for {measurement} seconds (warmup: {warmup}s)...")
        logger.info(f"{progress_msg} Workload will output progress every second during measurement period")
        output, exit_code = self.run_workload(
            public_ip, optimized_workload, workload_args, private_key=private_key, verbose=True
        )
        
        if exit_code != 0:
            logger.warning(f"Workload exited with code {exit_code}")
        
        # Wait for metrics collection to complete
        metric_thread.join(timeout=120)
        
        # Parse workload output
        workload_data = self.parse_workload_output(output, workload_name)
        
        # Get collected metrics
        metrics = self.collected_metrics.get(instance_type, {})
        
        # Calculate energy
        cpu_util = metrics.get("average_cpu_percent", 0)
        duration = self.workload_config["measurement_seconds"]
        gpu_power = metrics.get("average_gpu_power_watts")
        
        energy_joules = self.metric_collector.estimate_energy(
            instance_type, instance_config, cpu_util, duration, gpu_power
        )
        
        # Prepare results
        result = {
            "instance_type": instance_type,
            "workload": workload_name,
            "instance_id": instance_id,
            "public_ip": public_ip,
            "measurement_start": measurement_start.isoformat(),
            "measurement_duration_seconds": duration,
            "workload_output": workload_data,
            "metrics": metrics,
            "energy_joules": energy_joules,
            "work_units_completed": workload_data.get("total_count", 0),
            "throughput_work_per_sec": workload_data.get("total_count", 0) / duration if duration > 0 else 0,
            "efficiency_joules_per_work": energy_joules / workload_data.get("total_count", 1) if workload_data.get("total_count", 0) > 0 else float('inf'),
            "instance_config": instance_config
        }
        
        # Save raw logs
        log_file = self.results_dir / "raw_logs" / f"{instance_type}_{workload_name}.json"
        with open(log_file, "w") as f:
            json.dump(result, f, indent=2)
        
        progress_msg = f"[{self.benchmark_counter}/{self.total_benchmarks}]"
        logger.info(f"{progress_msg} ✓ Benchmark completed: {instance_type} / {workload_name}")
        logger.info(f"{progress_msg}   Work units: {workload_data.get('total_count', 0)}")
        logger.info(f"{progress_msg}   Throughput: {result['throughput_work_per_sec']:.2f} work/sec")
        logger.info(f"{progress_msg}   Energy: {energy_joules:.2f} Joules")
        logger.info(f"{progress_msg}   Efficiency: {result['efficiency_joules_per_work']:.4f} Joules/work")
        
        return result
    
    def run_all_benchmarks(self, iam_role_name: Optional[str] = None, parallel: bool = True, 
                          skip_unavailable: bool = True, only_arm_x86: bool = False) -> List[Dict]:
        """Run all benchmarks for all instance/workload combinations.
        
        If parallel=True, launches all instances at once and runs workloads sequentially on each.
        If parallel=False, runs instances and workloads sequentially.
        If skip_unavailable=True, skip instance types that fail to provision.
        """
        results = []
        
        instance_types = list(self.instance_config["instances"].keys())
        workloads = list(self.workload_config["workloads"].keys())
        
        # Filter to only ARM and x86 if requested
        if only_arm_x86:
            instance_types = [
                it for it in instance_types 
                if self.instance_config["instances"][it]["category"] in ["ARM", "x86"]
            ]
            logger.info("=" * 70)
            logger.info("FILTERING: Only running on ARM and x86 instances (GPU/FPGA skipped)")
            logger.info(f"Selected instances: {', '.join(instance_types)}")
            logger.info("=" * 70)
        
        # Test instance availability first if skip_unavailable is True
        available_instances = instance_types
        if skip_unavailable:
            logger.info("Note: Unavailable instances will be skipped automatically during provisioning")
        
        # Calculate total benchmarks
        if parallel:
            self.total_benchmarks = len(instance_types) * len(workloads)
        else:
            self.total_benchmarks = len(instance_types) * len(workloads)
        
        self.benchmark_counter = 0
        
        logger.info("=" * 70)
        logger.info(f"BENCHMARK SUITE: {len(instance_types)} instance types × {len(workloads)} workloads = {self.total_benchmarks} benchmarks")
        logger.info(f"Instance types: {', '.join(instance_types)}")
        logger.info(f"Workloads: {', '.join(workloads)}")
        logger.info(f"Mode: {'Parallel (instances)' if parallel else 'Sequential'}")
        logger.info("=" * 70)
        
        if parallel:
            # Launch all instances in parallel, then run workloads sequentially on each
            logger.info(f"Launching {len(available_instances)} instances in parallel...")
            
            def run_instance_benchmarks(instance_type):
                """Run all workloads on a single instance."""
                try:
                    return self.run_workloads_on_instance(instance_type, workloads, iam_role_name)
                except Exception as e:
                    logger.error(f"Failed to run benchmarks on {instance_type}: {e}")
                    return []
            
            # Run instances in parallel using threads
            threads = []
            thread_results = {}
            
            def worker(instance_type):
                thread_results[instance_type] = run_instance_benchmarks(instance_type)
            
            for instance_type in available_instances:
                thread = threading.Thread(target=worker, args=(instance_type,))
                thread.start()
                threads.append(thread)
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Collect all results
            for instance_type in available_instances:
                if instance_type in thread_results:
                    results.extend(thread_results[instance_type])
            
            logger.info("=" * 70)
            logger.info(f"ALL BENCHMARKS COMPLETED: {len(results)}/{self.total_benchmarks} successful")
            logger.info("=" * 70)
        else:
            # Sequential execution (original behavior)
            for instance_type in available_instances:
                logger.info(f"--- Processing instance type: {instance_type} ---")
                for workload_name in workloads:
                    try:
                        result = self.run_benchmark(instance_type, workload_name, iam_role_name)
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Failed benchmark {instance_type} / {workload_name}: {e}")
                        self.benchmark_counter += 1  # Count failed benchmarks too
                        continue
            
            logger.info("=" * 70)
            logger.info(f"ALL BENCHMARKS COMPLETED: {len(results)}/{self.total_benchmarks} successful")
            logger.info("=" * 70)
        
        return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run blockchain consensus benchmarks")
    parser.add_argument("--instance", help="Specific instance type to test")
    parser.add_argument("--workload", help="Specific workload to test")
    parser.add_argument("--iam-role", help="IAM role name for instances")
    parser.add_argument("--config", default="config/instances.json", help="Instance config path")
    parser.add_argument("--workload-config", default="config/workloads.json", help="Workload config path")
    parser.add_argument("--results", default="results", help="Results directory")
    parser.add_argument("--parallel", action="store_true", default=True, help="Run instances in parallel")
    parser.add_argument("--sequential", action="store_true", help="Run instances sequentially")
    parser.add_argument("--only-arm-x86", action="store_true", help="Only run on ARM and x86 instances (skip GPU/FPGA)")
    
    args = parser.parse_args()
    
    # Set up logging first
    results_dir = args.results
    log_file = setup_logging(results_dir)
    
    runner = BenchmarkRunner(args.config, args.workload_config, results_dir)
    
    # Set only_arm_x86 flag if requested
    if args.only_arm_x86:
        runner.only_arm_x86 = True
    
    if args.instance and args.workload:
        # Single benchmark mode
        runner.total_benchmarks = 1
        runner.benchmark_counter = 0
        result = runner.run_benchmark(args.instance, args.workload, args.iam_role)
        print(json.dumps(result, indent=2))
    else:
        parallel = args.parallel and not args.sequential
        results = runner.run_all_benchmarks(args.iam_role, parallel=parallel, only_arm_x86=args.only_arm_x86)
        print(f"Completed {len(results)} benchmarks")

