#!/usr/bin/env python3
"""
Generate seaborn visualizations for benchmark results.
"""
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional
import numpy as np

# Set seaborn style
sns.set_style("whitegrid")
sns.set_palette("husl")

def load_summary(summary_path: str = "results/summary.csv") -> pd.DataFrame:
    """Load summary data."""
    return pd.read_csv(summary_path)

def generate_performance_bar_plot(df: pd.DataFrame, workload: str, output_dir: Path):
    """Generate bar plot for performance (work/sec) by instance type."""
    workload_df = df[df["workload"] == workload].copy()
    
    if workload_df.empty:
        print(f"No data for workload {workload}")
        return
    
    plt.figure(figsize=(10, 6))
    workload_df = workload_df.sort_values("throughput_work_per_sec", ascending=False)
    
    ax = sns.barplot(data=workload_df, x="instance_type", y="throughput_work_per_sec")
    ax.set_title(f"Performance: {workload.upper()} - Throughput (work/sec) by Instance Type", fontsize=14, fontweight='bold')
    ax.set_xlabel("Instance Type", fontsize=12)
    ax.set_ylabel("Throughput (work/sec)", fontsize=12)
    ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    output_file = output_dir / f"performance_{workload}.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated performance plot: {output_file}")

def generate_efficiency_bar_plot(df: pd.DataFrame, workload: str, output_dir: Path):
    """Generate bar plot for efficiency (joules/work) by instance type."""
    workload_df = df[df["workload"] == workload].copy()
    
    if workload_df.empty:
        return
    
    # Filter out infinite values
    workload_df = workload_df[workload_df["efficiency_joules_per_work"] != float('inf')]
    
    if workload_df.empty:
        print(f"No valid efficiency data for workload {workload}")
        return
    
    plt.figure(figsize=(10, 6))
    workload_df = workload_df.sort_values("efficiency_joules_per_work", ascending=True)
    
    ax = sns.barplot(data=workload_df, x="instance_type", y="efficiency_joules_per_work")
    ax.set_title(f"Efficiency: {workload.upper()} - Energy per Work Unit (Joules/work) by Instance Type", fontsize=14, fontweight='bold')
    ax.set_xlabel("Instance Type", fontsize=12)
    ax.set_ylabel("Efficiency (Joules/work)", fontsize=12)
    ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    output_file = output_dir / f"efficiency_{workload}.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated efficiency plot: {output_file}")

def generate_cost_bar_plot(df: pd.DataFrame, workload: str, output_dir: Path):
    """Generate bar plot for cost efficiency (USD/work) by instance type."""
    workload_df = df[df["workload"] == workload].copy()
    
    if workload_df.empty:
        return
    
    # Filter out infinite values
    workload_df = workload_df[workload_df["cost_per_work_usd"] != float('inf')]
    
    if workload_df.empty:
        print(f"No valid cost data for workload {workload}")
        return
    
    plt.figure(figsize=(10, 6))
    workload_df = workload_df.sort_values("cost_per_work_usd", ascending=True)
    
    ax = sns.barplot(data=workload_df, x="instance_type", y="cost_per_work_usd")
    ax.set_title(f"Cost Efficiency: {workload.upper()} - Cost per Work Unit (USD/work) by Instance Type", fontsize=14, fontweight='bold')
    ax.set_xlabel("Instance Type", fontsize=12)
    ax.set_ylabel("Cost per Work Unit (USD/work)", fontsize=12)
    ax.tick_params(axis='x', rotation=45)
    
    # Format y-axis to show small values
    ax.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
    
    plt.tight_layout()
    output_file = output_dir / f"cost_{workload}.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated cost plot: {output_file}")

def generate_utilization_line_plot(df: pd.DataFrame, workload: str, instance_type: str, output_dir: Path):
    """Generate line plot for resource utilization over time."""
    # Note: This would require time-series data from raw logs
    # For now, we'll create a simple comparison bar chart
    workload_df = df[(df["workload"] == workload) & (df["instance_type"] == instance_type)].copy()
    
    if workload_df.empty:
        return
    
    plt.figure(figsize=(10, 6))
    
    # Create comparison of average utilization
    metrics = ["average_cpu_percent", "memory_usage_percent"]
    labels = ["CPU Utilization (%)", "Memory Utilization (%)"]
    values = [workload_df["average_cpu_percent"].iloc[0] if len(workload_df) > 0 else 0,
              workload_df["memory_usage_percent"].iloc[0] if len(workload_df) > 0 else 0]
    
    ax = sns.barplot(x=labels, y=values)
    ax.set_title(f"Resource Utilization: {workload.upper()} on {instance_type}", fontsize=14, fontweight='bold')
    ax.set_ylabel("Utilization (%)", fontsize=12)
    ax.set_ylim(0, 100)
    
    plt.tight_layout()
    output_file = output_dir / f"utilization_{workload}_{instance_type.replace('.', '_')}.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated utilization plot: {output_file}")

def generate_comparison_plot(df: pd.DataFrame, output_dir: Path):
    """Generate comparison plot across all workloads and instance types."""
    # Create a heatmap of throughput
    pivot = df.pivot_table(values="throughput_work_per_sec", 
                          index="instance_type", 
                          columns="workload", 
                          aggfunc="mean")
    
    if pivot.empty:
        return
    
    plt.figure(figsize=(12, 8))
    ax = sns.heatmap(pivot, annot=True, fmt='.2f', cmap="YlOrRd", cbar_kws={'label': 'Throughput (work/sec)'})
    ax.set_title("Performance Heatmap: Throughput (work/sec) Across Workloads and Instance Types", 
                fontsize=14, fontweight='bold')
    ax.set_xlabel("Workload", fontsize=12)
    ax.set_ylabel("Instance Type", fontsize=12)
    
    plt.tight_layout()
    output_file = output_dir / "comparison_heatmap.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated comparison heatmap: {output_file}")

def generate_all_graphs(summary_path: str = "results/summary.csv", output_dir: str = "results/graphs"):
    """Generate all visualizations."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df = load_summary(summary_path)
    
    if df.empty:
        print("No data to generate graphs from")
        return
    
    # Generate plots for each workload
    workloads = df["workload"].unique()
    for workload in workloads:
        generate_performance_bar_plot(df, workload, output_dir)
        generate_efficiency_bar_plot(df, workload, output_dir)
        generate_cost_bar_plot(df, workload, output_dir)
        
        # Generate utilization plots for each instance type
        instance_types = df[df["workload"] == workload]["instance_type"].unique()
        for instance_type in instance_types:
            generate_utilization_line_plot(df, workload, instance_type, output_dir)
    
    # Generate comparison heatmap
    generate_comparison_plot(df, output_dir)
    
    print(f"\nGenerated all graphs in {output_dir}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate benchmark result graphs")
    parser.add_argument("--summary", default="results/summary.csv", help="Summary CSV path")
    parser.add_argument("--output", default="results/graphs", help="Output directory")
    
    args = parser.parse_args()
    generate_all_graphs(args.summary, args.output)

