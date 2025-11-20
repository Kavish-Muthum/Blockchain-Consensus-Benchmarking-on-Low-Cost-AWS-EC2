#!/usr/bin/env python3
"""
Data aggregation and normalization for benchmark results.
"""
import json
import sys
import pandas as pd
from pathlib import Path
from typing import List, Dict

def load_benchmark_results(results_dir: str = "results/raw_logs") -> List[Dict]:
    """Load all benchmark results from raw logs."""
    results_dir = Path(results_dir)
    results = []
    
    for log_file in results_dir.glob("*.json"):
        try:
            with open(log_file) as f:
                result = json.load(f)
                results.append(result)
        except Exception as e:
            print(f"Error loading {log_file}: {e}")
            continue
    
    return results

def estimate_energy_fixed(instance_config: Dict, cpu_utilization_percent: float, 
                          duration_seconds: float) -> float:
    """
    Estimate energy consumption with fixed formula that includes idle power.
    This ensures energy is non-zero even when CPU utilization is 0.
    """
    from typing import Dict
    
    # Base power consumption (TDP)
    base_power_watts = instance_config.get("estimated_tdp_watts", 50)
    
    # Minimum base power (idle consumption ~30% of TDP)
    idle_power_watts = base_power_watts * 0.30
    
    # Active power scales with CPU utilization (remaining 70% of TDP)
    active_power_watts = (base_power_watts * 0.70) * (cpu_utilization_percent / 100.0)
    
    # Total power = idle + active
    total_power_watts = idle_power_watts + active_power_watts
    
    # Calculate energy in Joules (Watts × seconds)
    energy_joules = total_power_watts * duration_seconds
    
    return energy_joules

def normalize_results(results: List[Dict]) -> pd.DataFrame:
    """Normalize and aggregate benchmark results."""
    normalized = []
    
    for result in results:
        instance_type = result["instance_type"]
        workload = result["workload"]
        instance_config = result.get("instance_config", {})
        metrics = result.get("metrics", {})
        
        # Extract metrics
        work_units = result.get("work_units_completed", 0)
        duration = result.get("measurement_duration_seconds", 0)
        
        # Recalculate energy using fixed formula (includes idle power)
        cpu_util = metrics.get("average_cpu_percent", 0)
        energy_joules = estimate_energy_fixed(instance_config, cpu_util, duration)
        
        # Calculate normalized metrics
        throughput = result.get("throughput_work_per_sec", 0)
        
        # Use effective_vcpu if available (for single-threaded workloads), otherwise use actual vCPU
        effective_vcpu = instance_config.get("effective_vcpu") or instance_config.get("vCPU", 1)
        throughput_per_vcpu = throughput / effective_vcpu if effective_vcpu > 0 else 0
        
        # Recalculate efficiency based on corrected energy
        if work_units > 0 and energy_joules > 0:
            efficiency = energy_joules / work_units
        else:
            efficiency = float('inf')
        
        efficiency_per_vcpu = efficiency / effective_vcpu if effective_vcpu > 0 and efficiency != float('inf') else float('inf')
        
        # Also calculate per-core metrics for comparison
        actual_vcpu = instance_config.get("vCPU", 1)
        throughput_per_core = throughput / actual_vcpu if actual_vcpu > 0 else 0
        efficiency_per_core = efficiency / actual_vcpu if actual_vcpu > 0 and efficiency != float('inf') else float('inf')
        
        # Cost efficiency
        hourly_cost = instance_config.get("hourly_cost_usd", 0)
        duration_hours = duration / 3600.0
        cost_per_work = (hourly_cost * duration_hours) / work_units if work_units > 0 else float('inf')
        
        # Resource utilization
        avg_cpu = metrics.get("average_cpu_percent", 0)
        max_cpu = metrics.get("max_cpu_percent", 0)
        memory_usage = metrics.get("memory_usage_percent", 0)
        memory_used_mb = metrics.get("memory_used_mb", 0)
        memory_total_mb = metrics.get("memory_total_mb", 0)
        
        # GPU metrics if available
        avg_gpu = metrics.get("average_gpu_percent", 0)
        avg_gpu_power = metrics.get("average_gpu_power_watts", 0)
        
        normalized.append({
            "instance_type": instance_type,
            "architecture": instance_config.get("architecture", "unknown"),
            "category": instance_config.get("category", "unknown"),
            "vCPU": instance_config.get("vCPU", 0),
            "memory_gb": instance_config.get("memory_gb", 0),
            "workload": workload,
            "work_units_completed": work_units,
            "measurement_duration_seconds": duration,
            "throughput_work_per_sec": throughput,
            "throughput_per_vcpu": throughput_per_vcpu,
            "throughput_per_core": throughput_per_core,
            "energy_joules": energy_joules,
            "efficiency_joules_per_work": efficiency,
            "efficiency_per_vcpu": efficiency_per_vcpu,
            "efficiency_per_core": efficiency_per_core,
            "effective_vcpu": effective_vcpu,
            "actual_vcpu": actual_vcpu,
            "hourly_cost_usd": hourly_cost,
            "cost_per_work_usd": cost_per_work,
            "average_cpu_percent": avg_cpu,
            "max_cpu_percent": max_cpu,
            "memory_usage_percent": memory_usage,
            "memory_used_mb": memory_used_mb,
            "memory_total_mb": memory_total_mb,
            "average_gpu_percent": avg_gpu,
            "average_gpu_power_watts": avg_gpu_power,
            "instance_id": result.get("instance_id", ""),
            "measurement_start": result.get("measurement_start", "")
        })
    
    return pd.DataFrame(normalized)

def generate_summary(results_dir: str = "results"):
    """Generate summary JSON and CSV files."""
    results_dir = Path(results_dir)
    raw_logs_dir = results_dir / "raw_logs"
    
    # Load and normalize results
    results = load_benchmark_results(str(raw_logs_dir))
    if not results:
        print("No benchmark results found")
        return
    
    df = normalize_results(results)
    
    # Save summary JSON
    summary_json = results_dir / "summary.json"
    df.to_json(summary_json, orient="records", indent=2)
    print(f"Saved summary JSON: {summary_json}")
    
    # Save summary CSV
    summary_csv = results_dir / "summary.csv"
    df.to_csv(summary_csv, index=False)
    print(f"Saved summary CSV: {summary_csv}")
    
    # Print summary statistics
    print("\n=== Summary Statistics ===")
    print(f"Total benchmarks: {len(df)}")
    print(f"Instance types: {df['instance_type'].nunique()}")
    print(f"Workloads: {df['workload'].nunique()}")
    print("\nThroughput by instance type:")
    print(df.groupby("instance_type")["throughput_work_per_sec"].mean().sort_values(ascending=False))
    print("\nEfficiency by instance type:")
    print(df.groupby("instance_type")["efficiency_joules_per_work"].mean().sort_values())
    
    return df

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Normalize benchmark results")
    parser.add_argument("--results", default="results", help="Results directory")
    
    args = parser.parse_args()
    generate_summary(args.results)

