#!/usr/bin/env python3
"""
Create a PNG image of the comparison table.
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
import numpy as np

def create_comparison_table_png(summary_csv='results/summary.csv', output_png='results/comparison_table.png'):
    """Create a PNG image of the comparison table."""
    
    # Load data
    df = pd.read_csv(summary_csv)
    main_workloads = ['pow', 'pos', 'bft', 'zk']
    main_instances = ['t4g.2xlarge', 't3.2xlarge']
    
    # Filter data
    filtered = df[
        (df['instance_type'].isin(main_instances)) & 
        (df['workload'].isin(main_workloads))
    ].copy()
    
    # Prepare data for table
    table_data = []
    headers = ['Workload', 'Metric', 'ARM (t4g.2xlarge)', 'x86 (t3.2xlarge)']
    
    for workload in main_workloads:
        arm_data = filtered[(filtered['instance_type'] == 't4g.2xlarge') & (filtered['workload'] == workload)]
        x86_data = filtered[(filtered['instance_type'] == 't3.2xlarge') & (filtered['workload'] == workload)]
        
        if not arm_data.empty and not x86_data.empty:
            arm = arm_data.iloc[0]
            x86 = x86_data.iloc[0]
            
            # Workload header
            table_data.append([workload.upper(), '', '', ''])
            
            # Throughput
            arm_val = f"{arm['throughput_work_per_sec']:,.0f}"
            x86_val = f"{x86['throughput_work_per_sec']:,.0f}"
            table_data.append(['', 'Throughput (work/sec)', arm_val, x86_val])
            
            # Energy
            arm_val = f"{arm['energy_joules']:,.1f}"
            x86_val = f"{x86['energy_joules']:,.1f}"
            table_data.append(['', 'Energy (Joules)', arm_val, x86_val])
            
            # Energy Efficiency
            arm_val = f"{arm['efficiency_joules_per_work']:.2e}"
            x86_val = f"{x86['efficiency_joules_per_work']:.2e}"
            table_data.append(['', 'Energy Efficiency (J/work)', arm_val, x86_val])
            
            # Cost Efficiency
            arm_val = f"{arm['cost_per_work_usd']:.2e}"
            x86_val = f"{x86['cost_per_work_usd']:.2e}"
            table_data.append(['', 'Cost Efficiency (USD/work)', arm_val, x86_val])
            
            # Performance per vCPU
            arm_val = f"{arm['throughput_per_vcpu']:,.1f}"
            x86_val = f"{x86['throughput_per_vcpu']:,.1f}"
            table_data.append(['', 'Performance per vCPU', arm_val, x86_val])
            
            # Empty row
            table_data.append(['', '', '', ''])
    
    # Create figure with better sizing
    fig, ax = plt.subplots(figsize=(14, 9))
    ax.axis('tight')
    ax.axis('off')
    
    # Create table
    table = ax.table(cellText=table_data, colLabels=headers, cellLoc='left', loc='center',
                    colWidths=[0.18, 0.38, 0.22, 0.22])
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2.2)
    
    # Style header row
    header_color = '#2E5090'
    for i in range(len(headers)):
        cell = table[(0, i)]
        cell.set_facecolor(header_color)
        cell.set_text_props(weight='bold', color='white', fontsize=11)
        cell.set_edgecolor('white')
        cell.set_linewidth(1.5)
    
    # Style cells
    for i in range(len(table_data) + 1):
        for j in range(len(headers)):
            cell = table[(i, j)]
            cell.set_edgecolor('#E7E6E6')
            cell.set_linewidth(0.8)
            
            # Alternate row colors
            if i > 0 and i % 2 == 0:
                cell.set_facecolor('#F2F2F2')
            else:
                cell.set_facecolor('white')
    
    # Style workload headers
    workload_color = '#D0DEEF'
    for i, row in enumerate(table_data):
        if row[0] and row[1] == '':  # Workload header row
            for j in range(len(headers)):
                cell = table[(i+1, j)]
                cell.set_facecolor(workload_color)
                cell.set_text_props(weight='bold', fontsize=11)
                cell.set_edgecolor('#B8C9E8')
                cell.set_linewidth(1.2)
    
    # Highlight better values (green for ARM, blue for x86 where appropriate)
    arm_green = '#E2EFDA'  # Light green
    x86_blue = '#DEEBF7'   # Light blue
    
    for i, row in enumerate(table_data):
        if row[1] and row[1] != '':  # Data row
            metric = row[1].lower()
            
            # For efficiency metrics, ARM is always better
            if 'efficiency' in metric or 'energy' in metric:
                if 'cost' not in metric or 'energy (joules)' in metric:
                    cell = table[(i+1, 2)]  # ARM column
                    cell.set_facecolor(arm_green)
            
            # For throughput, compare values
            elif 'throughput' in metric or 'performance' in metric:
                try:
                    arm_val = float(row[2].replace(',', ''))
                    x86_val = float(row[3].replace(',', ''))
                    if arm_val > x86_val:
                        cell = table[(i+1, 2)]  # ARM column
                        cell.set_facecolor(arm_green)
                    elif x86_val > arm_val:
                        cell = table[(i+1, 3)]  # x86 column
                        cell.set_facecolor(x86_blue)
                except:
                    pass
    
    # Title
    title = plt.suptitle('Benchmark Results Comparison: ARM vs x86\nBlockchain Consensus Workloads on 8 vCPU Instances', 
                         fontsize=16, fontweight='bold', y=0.975)
    
    # Subtitle
    subtitle = fig.text(0.5, 0.94, 't4g.2xlarge (ARM) vs t3.2xlarge (x86) | Duration: 300 seconds', 
                       ha='center', fontsize=11, style='italic', color='#555555')
    
    # Footer
    footer_text = 'Energy values estimated from TDP and CPU utilization. Lower values are better for efficiency metrics.'
    fig.text(0.5, 0.02, footer_text, ha='center', fontsize=9, style='italic', color='#777777')
    
    # Adjust layout
    plt.tight_layout()
    plt.subplots_adjust(top=0.90, bottom=0.05)
    
    # Save
    plt.savefig(output_png, dpi=300, bbox_inches='tight', pad_inches=0.3, facecolor='white')
    print(f"✓ Created: {output_png}")
    plt.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Create comparison table PNG")
    parser.add_argument("--input", default="results/summary.csv", help="Input CSV file")
    parser.add_argument("--output", default="results/comparison_table.png", help="Output PNG file")
    args = parser.parse_args()
    create_comparison_table_png(args.input, args.output)

