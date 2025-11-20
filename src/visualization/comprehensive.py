#!/usr/bin/env python3
"""
Generate comprehensive comparison graphs showing all benchmark results.
"""
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np

# Set seaborn style
sns.set_style("whitegrid")
sns.set_palette("husl")

def load_summary(summary_path: str = "results/summary.csv") -> pd.DataFrame:
    """Load summary data."""
    return pd.read_csv(summary_path)

def generate_comprehensive_comparison(df: pd.DataFrame, output_dir: Path):
    """Generate a single comprehensive comparison graph with all metrics."""
    
    # Filter to ARM and x86 8 vCPU instances only
    df_filtered = df[df['instance_type'].isin(['t4g.2xlarge', 't3.2xlarge'])].copy()
    
    # Filter out workloads with 0 work units
    df_filtered = df_filtered[df_filtered['workload'].isin(['pow', 'pos', 'bft', 'zk'])].copy()
    
    if df_filtered.empty:
        print("No data available for comprehensive comparison")
        return
    
    # Create figure with subplots
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
    
    # 1. Performance Comparison (Throughput)
    ax1 = fig.add_subplot(gs[0, 0])
    performance_data = df_filtered.pivot_table(
        values='throughput_work_per_sec',
        index='workload',
        columns='instance_type',
        aggfunc='mean'
    )
    
    x = np.arange(len(performance_data.index))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, performance_data['t4g.2xlarge'], width, label='ARM (t4g.2xlarge)', color='#3498db')
    bars2 = ax1.bar(x + width/2, performance_data['t3.2xlarge'], width, label='x86 (t3.2xlarge)', color='#e74c3c')
    
    ax1.set_xlabel('Workload', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Throughput (work/sec)', fontsize=12, fontweight='bold')
    ax1.set_title('Performance Comparison: ARM vs x86', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(performance_data.index, rotation=0)
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:,.0f}',
                    ha='center', va='bottom', fontsize=8)
    
    # 2. Energy Efficiency Comparison
    ax2 = fig.add_subplot(gs[0, 1])
    efficiency_data = df_filtered[df_filtered['efficiency_joules_per_work'] != float('inf')].pivot_table(
        values='efficiency_joules_per_work',
        index='workload',
        columns='instance_type',
        aggfunc='mean'
    )
    
    bars3 = ax2.bar(x[:len(efficiency_data.index)] - width/2, efficiency_data['t4g.2xlarge'], width, 
                    label='ARM (t4g.2xlarge)', color='#2ecc71')
    bars4 = ax2.bar(x[:len(efficiency_data.index)] + width/2, efficiency_data['t3.2xlarge'], width, 
                    label='x86 (t3.2xlarge)', color='#e67e22')
    
    ax2.set_xlabel('Workload', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Energy Efficiency (Joules/work)', fontsize=12, fontweight='bold')
    ax2.set_title('Energy Efficiency Comparison: ARM vs x86', fontsize=14, fontweight='bold')
    ax2.set_xticks(x[:len(efficiency_data.index)])
    ax2.set_xticklabels(efficiency_data.index, rotation=0)
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)
    ax2.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
    
    # Add value labels
    for bars in [bars3, bars4]:
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2e}',
                    ha='center', va='bottom', fontsize=8)
    
    # 3. Cost Efficiency Comparison
    ax3 = fig.add_subplot(gs[0, 2])
    cost_data = df_filtered[df_filtered['cost_per_work_usd'] != float('inf')].pivot_table(
        values='cost_per_work_usd',
        index='workload',
        columns='instance_type',
        aggfunc='mean'
    )
    
    bars5 = ax3.bar(x[:len(cost_data.index)] - width/2, cost_data['t4g.2xlarge'], width, 
                    label='ARM (t4g.2xlarge)', color='#9b59b6')
    bars6 = ax3.bar(x[:len(cost_data.index)] + width/2, cost_data['t3.2xlarge'], width, 
                    label='x86 (t3.2xlarge)', color='#f39c12')
    
    ax3.set_xlabel('Workload', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Cost per Work Unit (USD/work)', fontsize=12, fontweight='bold')
    ax3.set_title('Cost Efficiency Comparison: ARM vs x86', fontsize=14, fontweight='bold')
    ax3.set_xticks(x[:len(cost_data.index)])
    ax3.set_xticklabels(cost_data.index, rotation=0)
    ax3.legend()
    ax3.grid(axis='y', alpha=0.3)
    ax3.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
    
    # Add value labels
    for bars in [bars5, bars6]:
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2e}',
                    ha='center', va='bottom', fontsize=8)
    
    # 4. Energy Consumption (Total)
    ax4 = fig.add_subplot(gs[1, 0])
    energy_data = df_filtered.pivot_table(
        values='energy_joules',
        index='workload',
        columns='instance_type',
        aggfunc='mean'
    )
    
    bars7 = ax4.bar(x - width/2, energy_data['t4g.2xlarge'], width, 
                    label='ARM (t4g.2xlarge)', color='#16a085')
    bars8 = ax4.bar(x + width/2, energy_data['t3.2xlarge'], width, 
                    label='x86 (t3.2xlarge)', color='#d35400')
    
    ax4.set_xlabel('Workload', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Energy Consumption (Joules)', fontsize=12, fontweight='bold')
    ax4.set_title('Total Energy Consumption: ARM vs x86', fontsize=14, fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels(energy_data.index, rotation=0)
    ax4.legend()
    ax4.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bars in [bars7, bars8]:
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.0f}',
                    ha='center', va='bottom', fontsize=8)
    
    # 5. Performance per vCPU
    ax5 = fig.add_subplot(gs[1, 1])
    perf_vcpu_data = df_filtered.pivot_table(
        values='throughput_per_vcpu',
        index='workload',
        columns='instance_type',
        aggfunc='mean'
    )
    
    bars9 = ax5.bar(x - width/2, perf_vcpu_data['t4g.2xlarge'], width, 
                    label='ARM (t4g.2xlarge)', color='#1abc9c')
    bars10 = ax5.bar(x + width/2, perf_vcpu_data['t3.2xlarge'], width, 
                     label='x86 (t3.2xlarge)', color='#c0392b')
    
    ax5.set_xlabel('Workload', fontsize=12, fontweight='bold')
    ax5.set_ylabel('Throughput per vCPU (work/sec/vCPU)', fontsize=12, fontweight='bold')
    ax5.set_title('Performance per vCPU: ARM vs x86', fontsize=14, fontweight='bold')
    ax5.set_xticks(x)
    ax5.set_xticklabels(perf_vcpu_data.index, rotation=0)
    ax5.legend()
    ax5.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bars in [bars9, bars10]:
        for bar in bars:
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:,.0f}',
                    ha='center', va='bottom', fontsize=8)
    
    # 6. Heatmap: Performance Across All Workloads
    ax6 = fig.add_subplot(gs[1, 2])
    heatmap_data = df_filtered.pivot_table(
        values='throughput_work_per_sec',
        index='instance_type',
        columns='workload',
        aggfunc='mean'
    )
    
    sns.heatmap(heatmap_data, annot=True, fmt='.0f', cmap='YlOrRd', 
                cbar_kws={'label': 'Throughput (work/sec)'}, ax=ax6)
    ax6.set_title('Performance Heatmap: Throughput by Instance and Workload', 
                  fontsize=14, fontweight='bold')
    ax6.set_xlabel('Workload', fontsize=12, fontweight='bold')
    ax6.set_ylabel('Instance Type', fontsize=12, fontweight='bold')
    
    # Overall title
    fig.suptitle('Comprehensive Benchmark Results: ARM vs x86 (8 vCPU)', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    output_file = output_dir / "comprehensive_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight', pad_inches=0.2)
    plt.close()
    print(f"Generated comprehensive comparison: {output_file}")

def generate_summary_table(df: pd.DataFrame, output_dir: Path):
    """Generate comprehensive summary table."""
    output_file = output_dir / "comprehensive_summary.md"
    
    # Filter to ARM and x86 8 vCPU instances
    df_filtered = df[df['instance_type'].isin(['t4g.2xlarge', 't3.2xlarge'])].copy()
    df_filtered = df_filtered[df_filtered['workload'].isin(['pow', 'pos', 'bft', 'zk'])].copy()
    
    with open(output_file, 'w') as f:
        f.write("# Comprehensive Benchmark Results Summary\n\n")
        f.write("## ARM vs x86 Performance Comparison (8 vCPU Instances)\n\n")
        
        # Performance Table
        f.write("### 1. Performance (Throughput)\n\n")
        f.write("| Workload | ARM (t4g.2xlarge) | x86 (t3.2xlarge) | Winner | Difference |\n")
        f.write("|----------|-------------------|------------------|--------|------------|\n")
        
        for workload in ['pow', 'pos', 'bft', 'zk']:
            wl_data = df_filtered[df_filtered['workload'] == workload]
            if not wl_data.empty:
                arm_row = wl_data[wl_data['instance_type'] == 't4g.2xlarge'].iloc[0]
                x86_row = wl_data[wl_data['instance_type'] == 't3.2xlarge'].iloc[0]
                
                arm_throughput = arm_row['throughput_work_per_sec']
                x86_throughput = x86_row['throughput_work_per_sec']
                
                if arm_throughput > x86_throughput:
                    winner = "ARM"
                    diff = f"+{((arm_throughput/x86_throughput - 1) * 100):.1f}%"
                else:
                    winner = "x86"
                    diff = f"+{((x86_throughput/arm_throughput - 1) * 100):.1f}%"
                
                f.write(f"| **{workload.upper()}** | {arm_throughput:,.2f} work/s | {x86_throughput:,.2f} work/s | {winner} | {diff} |\n")
        
        f.write("\n### 2. Energy Efficiency (Joules per Work Unit)\n\n")
        f.write("| Workload | ARM (t4g.2xlarge) | x86 (t3.2xlarge) | Winner | Improvement |\n")
        f.write("|----------|-------------------|------------------|--------|-------------|\n")
        
        for workload in ['pow', 'pos', 'bft', 'zk']:
            wl_data = df_filtered[df_filtered['workload'] == workload]
            wl_data = wl_data[wl_data['efficiency_joules_per_work'] != float('inf')]
            if not wl_data.empty:
                arm_row = wl_data[wl_data['instance_type'] == 't4g.2xlarge'].iloc[0]
                x86_row = wl_data[wl_data['instance_type'] == 't3.2xlarge'].iloc[0]
                
                arm_eff = arm_row['efficiency_joules_per_work']
                x86_eff = x86_row['efficiency_joules_per_work']
                
                if arm_eff < x86_eff:
                    winner = "ARM"
                    improvement = f"{((1 - arm_eff/x86_eff) * 100):.1f}% better"
                else:
                    winner = "x86"
                    improvement = f"{((1 - x86_eff/arm_eff) * 100):.1f}% better"
                
                f.write(f"| **{workload.upper()}** | {arm_eff:.2e} J/work | {x86_eff:.2e} J/work | {winner} | {improvement} |\n")
        
        f.write("\n### 3. Cost Efficiency (USD per Work Unit)\n\n")
        f.write("| Workload | ARM (t4g.2xlarge) | x86 (t3.2xlarge) | Winner | Savings |\n")
        f.write("|----------|-------------------|------------------|--------|----------|\n")
        
        for workload in ['pow', 'pos', 'bft', 'zk']:
            wl_data = df_filtered[df_filtered['workload'] == workload]
            wl_data = wl_data[wl_data['cost_per_work_usd'] != float('inf')]
            if not wl_data.empty:
                arm_row = wl_data[wl_data['instance_type'] == 't4g.2xlarge'].iloc[0]
                x86_row = wl_data[wl_data['instance_type'] == 't3.2xlarge'].iloc[0]
                
                arm_cost = arm_row['cost_per_work_usd']
                x86_cost = x86_row['cost_per_work_usd']
                
                if arm_cost < x86_cost:
                    winner = "ARM"
                    savings = f"{((1 - arm_cost/x86_cost) * 100):.1f}% cheaper"
                else:
                    winner = "x86"
                    savings = f"{((1 - x86_cost/arm_cost) * 100):.1f}% cheaper"
                
                f.write(f"| **{workload.upper()}** | ${arm_cost:.2e} | ${x86_cost:.2e} | {winner} | {savings} |\n")
        
        f.write("\n### 4. Total Energy Consumption\n\n")
        f.write("| Workload | ARM (t4g.2xlarge) | x86 (t3.2xlarge) | Difference |\n")
        f.write("|----------|-------------------|------------------|------------|\n")
        
        for workload in ['pow', 'pos', 'bft', 'zk']:
            wl_data = df_filtered[df_filtered['workload'] == workload]
            if not wl_data.empty:
                arm_row = wl_data[wl_data['instance_type'] == 't4g.2xlarge'].iloc[0]
                x86_row = wl_data[wl_data['instance_type'] == 't3.2xlarge'].iloc[0]
                
                arm_energy = arm_row['energy_joules']
                x86_energy = x86_row['energy_joules']
                diff = x86_energy - arm_energy
                diff_pct = (diff / x86_energy * 100) if x86_energy > 0 else 0
                
                f.write(f"| **{workload.upper()}** | {arm_energy:.2f} J | {x86_energy:.2f} J | {diff:.2f} J ({diff_pct:+.1f}%) |\n")
        
        f.write("\n### 5. Summary Statistics\n\n")
        f.write("| Metric | ARM (t4g.2xlarge) | x86 (t3.2xlarge) |\n")
        f.write("|--------|-------------------|------------------|\n")
        f.write(f"| **Average Throughput** | {df_filtered[df_filtered['instance_type']=='t4g.2xlarge']['throughput_work_per_sec'].mean():,.2f} work/s | {df_filtered[df_filtered['instance_type']=='t3.2xlarge']['throughput_work_per_sec'].mean():,.2f} work/s |\n")
        
        arm_avg_eff = df_filtered[(df_filtered['instance_type']=='t4g.2xlarge') & (df_filtered['efficiency_joules_per_work'] != float('inf'))]['efficiency_joules_per_work'].mean()
        x86_avg_eff = df_filtered[(df_filtered['instance_type']=='t3.2xlarge') & (df_filtered['efficiency_joules_per_work'] != float('inf'))]['efficiency_joules_per_work'].mean()
        f.write(f"| **Average Energy Efficiency** | {arm_avg_eff:.2e} J/work | {x86_avg_eff:.2e} J/work |\n")
        
        arm_avg_cost = df_filtered[(df_filtered['instance_type']=='t4g.2xlarge') & (df_filtered['cost_per_work_usd'] != float('inf'))]['cost_per_work_usd'].mean()
        x86_avg_cost = df_filtered[(df_filtered['instance_type']=='t3.2xlarge') & (df_filtered['cost_per_work_usd'] != float('inf'))]['cost_per_work_usd'].mean()
        f.write(f"| **Average Cost Efficiency** | ${arm_avg_cost:.2e} | ${x86_avg_cost:.2e} |\n")
        
        f.write(f"| **Average Energy Consumption** | {df_filtered[df_filtered['instance_type']=='t4g.2xlarge']['energy_joules'].mean():.2f} J | {df_filtered[df_filtered['instance_type']=='t3.2xlarge']['energy_joules'].mean():.2f} J |\n")
    
    print(f"Generated comprehensive summary table: {output_file}")

def generate_all(summary_path: str = "results/summary.csv", output_dir: str = "results"):
    """Generate comprehensive graphs and tables."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df = load_summary(summary_path)
    
    if df.empty:
        print("No data available")
        return
    
    # Generate comprehensive comparison graph
    generate_comprehensive_comparison(df, output_dir)
    
    # Generate summary table
    generate_summary_table(df, output_dir)
    
    print(f"\nGenerated comprehensive results in {output_dir}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate comprehensive benchmark comparison")
    parser.add_argument("--summary", default="results/summary.csv", help="Summary CSV path")
    parser.add_argument("--output", default="results", help="Output directory")
    
    args = parser.parse_args()
    generate_all(args.summary, args.output)

