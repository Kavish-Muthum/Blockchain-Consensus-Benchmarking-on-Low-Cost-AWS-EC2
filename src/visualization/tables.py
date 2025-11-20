#!/usr/bin/env python3
"""
Generate Markdown/CSV tables comparing results across instance types per workload.
"""
import pandas as pd
from pathlib import Path
from typing import Optional

def load_summary(summary_path: str = "results/summary.csv") -> pd.DataFrame:
    """Load summary data."""
    return pd.read_csv(summary_path)

def format_number(value, decimals=2, inf_str="N/A"):
    """Format number for display."""
    if pd.isna(value) or value == float('inf'):
        return inf_str
    if isinstance(value, float):
        return f"{value:.{decimals}f}"
    return str(value)

def generate_workload_table(df: pd.DataFrame, workload: str, output_dir: Path) -> str:
    """Generate table for a specific workload."""
    workload_df = df[df["workload"] == workload].copy()
    
    if workload_df.empty:
        return f"## {workload.upper()}\n\nNo data available.\n"
    
    # Sort by throughput
    workload_df = workload_df.sort_values("throughput_work_per_sec", ascending=False)
    
    markdown = f"## {workload.upper()}\n\n"
    markdown += "| Instance Type | Architecture | vCPU | Work Units | Duration (s) | "
    markdown += "Throughput (work/s) | Throughput/vCPU | CPU % | RAM % | "
    markdown += "Energy (J) | Efficiency (J/work) | Cost ($/work) |\n"
    markdown += "|" + "---|" * 12 + "\n"
    
    for _, row in workload_df.iterrows():
        markdown += f"| {row['instance_type']} | {row['architecture']} | {int(row['vCPU'])} | "
        markdown += f"{int(row['work_units_completed'])} | {int(row['measurement_duration_seconds'])} | "
        markdown += f"{format_number(row['throughput_work_per_sec'])} | "
        markdown += f"{format_number(row['throughput_per_vcpu'])} | "
        markdown += f"{format_number(row['average_cpu_percent'], 1)}% | "
        markdown += f"{format_number(row['memory_usage_percent'], 1)}% | "
        markdown += f"{format_number(row['energy_joules'])} | "
        markdown += f"{format_number(row['efficiency_joules_per_work'])} | "
        markdown += f"${format_number(row['cost_per_work_usd'], 6)} |\n"
    
    return markdown

def generate_summary_table(df: pd.DataFrame) -> str:
    """Generate overall summary table."""
    markdown = "# Benchmark Results Summary\n\n"
    markdown += "## Overview\n\n"
    markdown += f"Total benchmarks: {len(df)}\n\n"
    markdown += f"Instance types: {df['instance_type'].nunique()}\n\n"
    markdown += f"Workloads: {df['workload'].nunique()}\n\n"
    
    # Summary by instance type
    markdown += "## Average Performance by Instance Type\n\n"
    summary = df.groupby("instance_type").agg({
        "throughput_work_per_sec": "mean",
        "efficiency_joules_per_work": "mean",
        "cost_per_work_usd": "mean",
        "average_cpu_percent": "mean",
        "memory_usage_percent": "mean"
    }).round(4)
    
    markdown += "| Instance Type | Avg Throughput (work/s) | Avg Efficiency (J/work) | "
    markdown += "Avg Cost ($/work) | Avg CPU % | Avg RAM % |\n"
    markdown += "|" + "---|" * 6 + "\n"
    
    for instance_type, row in summary.iterrows():
        markdown += f"| {instance_type} | "
        markdown += f"{format_number(row['throughput_work_per_sec'])} | "
        markdown += f"{format_number(row['efficiency_joules_per_work'])} | "
        markdown += f"${format_number(row['cost_per_work_usd'], 6)} | "
        markdown += f"{format_number(row['average_cpu_percent'], 1)}% | "
        markdown += f"{format_number(row['memory_usage_percent'], 1)}% |\n"
    
    # Summary by workload
    markdown += "\n## Average Performance by Workload\n\n"
    workload_summary = df.groupby("workload").agg({
        "throughput_work_per_sec": "mean",
        "efficiency_joules_per_work": "mean",
        "cost_per_work_usd": "mean"
    }).round(4)
    
    markdown += "| Workload | Avg Throughput (work/s) | Avg Efficiency (J/work) | Avg Cost ($/work) |\n"
    markdown += "|" + "---|" * 4 + "\n"
    
    for workload, row in workload_summary.iterrows():
        markdown += f"| {workload} | "
        markdown += f"{format_number(row['throughput_work_per_sec'])} | "
        markdown += f"{format_number(row['efficiency_joules_per_work'])} | "
        markdown += f"${format_number(row['cost_per_work_usd'], 6)} |\n"
    
    return markdown

def generate_tables(summary_path: str = "results/summary.csv", output_dir: str = "results/tables"):
    """Generate all tables."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df = load_summary(summary_path)
    
    if df.empty:
        print("No data to generate tables from")
        return
    
    # Generate summary table
    summary_table = generate_summary_table(df)
    summary_file = output_dir / "summary.md"
    with open(summary_file, "w") as f:
        f.write(summary_table)
    print(f"Generated summary table: {summary_file}")
    
    # Generate per-workload tables
    workloads = df["workload"].unique()
    for workload in workloads:
        workload_table = generate_workload_table(df, workload, output_dir)
        workload_file = output_dir / f"workload_{workload}.md"
        with open(workload_file, "w") as f:
            f.write(workload_table)
        print(f"Generated workload table: {workload_file}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate benchmark result tables")
    parser.add_argument("--summary", default="results/summary.csv", help="Summary CSV path")
    parser.add_argument("--output", default="results/tables", help="Output directory")
    
    args = parser.parse_args()
    generate_tables(args.summary, args.output)

