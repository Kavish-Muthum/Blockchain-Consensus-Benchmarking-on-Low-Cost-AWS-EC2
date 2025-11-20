#!/usr/bin/env python3
"""
Generate comprehensive PDF report with test explanations, verbose logs, and result analysis.
"""
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from PIL import Image as PILImage
import io

class BenchmarkReportGenerator:
    """Generate comprehensive PDF reports from benchmark results."""
    
    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#283593'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#3949ab'),
            spaceAfter=8,
            spaceBefore=8
        ))
        
        # Note: BodyText already exists, so we modify it instead of adding
        # Or use the existing one without modification
        
        self.styles.add(ParagraphStyle(
            name='CodeText',
            parent=self.styles['Code'],
            fontSize=8,
            leading=10,
            fontName='Courier',
            leftIndent=20,
            rightIndent=20
        ))
    
    def load_results(self) -> Dict:
        """Load all benchmark results."""
        summary_json = self.results_dir / "summary.json"
        summary_csv = self.results_dir / "summary.csv"
        raw_logs_dir = self.results_dir / "raw_logs"
        
        results = {
            "summary_df": None,
            "raw_results": []
        }
        
        if summary_csv.exists():
            results["summary_df"] = pd.read_csv(summary_csv)
        
        if summary_json.exists():
            with open(summary_json) as f:
                results["summary_data"] = json.load(f)
        
        # Load raw logs
        for log_file in raw_logs_dir.glob("*.json"):
            try:
                with open(log_file) as f:
                    results["raw_results"].append(json.load(f))
            except Exception as e:
                print(f"Error loading {log_file}: {e}")
        
        return results
    
    def generate_summary_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate summary statistics."""
        if df is None or df.empty:
            return {}
        
        metrics = {}
        
        # Overall statistics
        metrics["total_benchmarks"] = len(df)
        metrics["instance_types"] = df["instance_type"].nunique()
        metrics["workloads"] = df["workload"].nunique()
        
        # Performance leaderboard
        if not df.empty:
            best_perf_row = df.loc[df["throughput_work_per_sec"].idxmax()]
            metrics["best_performance"] = best_perf_row.to_dict() if isinstance(best_perf_row, pd.Series) else best_perf_row
            worst_perf_row = df.loc[df["throughput_work_per_sec"].idxmin()]
            metrics["worst_performance"] = worst_perf_row.to_dict() if isinstance(worst_perf_row, pd.Series) else worst_perf_row
        else:
            metrics["best_performance"] = None
            metrics["worst_performance"] = None
        
        # Efficiency leaderboard
        efficiency_df = df[df["efficiency_joules_per_work"] != float('inf')]
        if not efficiency_df.empty:
            best_eff_row = efficiency_df.loc[efficiency_df["efficiency_joules_per_work"].idxmin()]
            metrics["best_efficiency"] = best_eff_row.to_dict() if isinstance(best_eff_row, pd.Series) else best_eff_row
            worst_eff_row = efficiency_df.loc[efficiency_df["efficiency_joules_per_work"].idxmax()]
            metrics["worst_efficiency"] = worst_eff_row.to_dict() if isinstance(worst_eff_row, pd.Series) else worst_eff_row
        else:
            metrics["best_efficiency"] = None
            metrics["worst_efficiency"] = None
        
        # Cost efficiency
        cost_df = df[df["cost_per_work_usd"] != float('inf')]
        if not cost_df.empty:
            best_cost_row = cost_df.loc[cost_df["cost_per_work_usd"].idxmin()]
            metrics["best_cost"] = best_cost_row.to_dict() if isinstance(best_cost_row, pd.Series) else best_cost_row
            worst_cost_row = cost_df.loc[cost_df["cost_per_work_usd"].idxmax()]
            metrics["worst_cost"] = worst_cost_row.to_dict() if isinstance(worst_cost_row, pd.Series) else worst_cost_row
        else:
            metrics["best_cost"] = None
            metrics["worst_cost"] = None
        
        # By workload analysis
        metrics["by_workload"] = {}
        for workload in df["workload"].unique():
            workload_df = df[df["workload"] == workload]
            metrics["by_workload"][workload] = {
                "avg_throughput": workload_df["throughput_work_per_sec"].mean(),
                "max_throughput": workload_df["throughput_work_per_sec"].max(),
                "min_efficiency": workload_df[workload_df["efficiency_joules_per_work"] != float('inf')]["efficiency_joules_per_work"].min() if not workload_df[workload_df["efficiency_joules_per_work"] != float('inf')].empty else None,
                "best_instance": workload_df.loc[workload_df["throughput_work_per_sec"].idxmax(), "instance_type"] if not workload_df.empty else None
            }
        
        return metrics
    
    def create_graph_images(self, df: pd.DataFrame, temp_dir: Path) -> List[Path]:
        """Create graph images for embedding in PDF."""
        graphs_dir = self.results_dir / "graphs"
        temp_dir.mkdir(exist_ok=True)
        
        graph_paths = []
        
        if df is None or df.empty:
            return graph_paths
        
        # Performance comparison graphs
        workloads = df["workload"].unique()
        sns.set_style("whitegrid")
        sns.set_palette("husl")
        
        for workload in workloads:
            workload_df = df[df["workload"] == workload].sort_values("throughput_work_per_sec", ascending=False)
            
            if workload_df.empty:
                continue
            
            # Performance bar plot
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.barplot(data=workload_df, x="instance_type", y="throughput_work_per_sec", ax=ax)
            ax.set_title(f"Performance: {workload.upper()} - Throughput (work/sec)", fontsize=14, fontweight='bold')
            ax.set_xlabel("Instance Type", fontsize=12)
            ax.set_ylabel("Throughput (work/sec)", fontsize=12)
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            
            perf_path = temp_dir / f"perf_{workload}.png"
            plt.savefig(perf_path, dpi=150, bbox_inches='tight')
            plt.close()
            graph_paths.append(perf_path)
            
            # Efficiency bar plot
            eff_df = workload_df[workload_df["efficiency_joules_per_work"] != float('inf')]
            if not eff_df.empty:
                fig, ax = plt.subplots(figsize=(8, 5))
                eff_df = eff_df.sort_values("efficiency_joules_per_work", ascending=True)
                sns.barplot(data=eff_df, x="instance_type", y="efficiency_joules_per_work", ax=ax)
                ax.set_title(f"Energy Efficiency: {workload.upper()} - Joules per Work Unit", fontsize=14, fontweight='bold')
                ax.set_xlabel("Instance Type", fontsize=12)
                ax.set_ylabel("Efficiency (Joules/work)", fontsize=12)
                ax.tick_params(axis='x', rotation=45)
                plt.tight_layout()
                
                eff_path = temp_dir / f"eff_{workload}.png"
                plt.savefig(eff_path, dpi=150, bbox_inches='tight')
                plt.close()
                graph_paths.append(eff_path)
        
        return graph_paths
    
    def format_table(self, df: pd.DataFrame, max_rows: int = 50) -> Table:
        """Format DataFrame as ReportLab Table."""
        if df is None or df.empty:
            return Table([["No data available"]])
        
        # Limit rows
        df_display = df.head(max_rows)
        
        # Convert to string, format numbers
        data = []
        headers = list(df_display.columns)
        data.append(headers)
        
        for _, row in df_display.iterrows():
            row_data = []
            for col in headers:
                val = row[col]
                if pd.isna(val) or val == float('inf'):
                    row_data.append("N/A")
                elif isinstance(val, float):
                    if abs(val) < 0.001:
                        row_data.append(f"{val:.2e}")
                    else:
                        row_data.append(f"{val:.4f}")
                else:
                    row_data.append(str(val))
            data.append(row_data)
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        return table
    
    def generate_report(self, output_path: str = "results/benchmark_report.pdf"):
        """Generate comprehensive PDF report."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load results
        results = self.load_results()
        df = results.get("summary_df")
        
        # Create temporary directory for graphs
        temp_dir = self.results_dir / "report_temp"
        temp_dir.mkdir(exist_ok=True)
        
        # Generate summary metrics
        metrics = self.generate_summary_metrics(df) if df is not None else {}
        
        # Create graph images
        graph_paths = self.create_graph_images(df, temp_dir) if df is not None else []
        
        # Build PDF
        doc = SimpleDocTemplate(str(output_path), pagesize=letter,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        story = []
        
        # Title Page
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph("Blockchain Consensus Benchmarking", self.styles['CustomTitle']))
        story.append(Paragraph("Performance and Energy Efficiency Analysis", self.styles['Heading2']))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.styles['Normal']))
        story.append(PageBreak())
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        story.append(Paragraph(
            f"This report presents comprehensive benchmarking results for blockchain consensus workloads "
            f"across multiple EC2 instance types. A total of {metrics.get('total_benchmarks', 0)} benchmarks "
            f"were executed across {metrics.get('instance_types', 0)} instance types and {metrics.get('workloads', 0)} "
            f"workload types, measuring both performance (throughput) and energy efficiency (joules per work unit).",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 0.2*inch))
        
        if metrics.get("best_performance") is not None:
            best = metrics["best_performance"]
            instance_type = best.get('instance_type', 'N/A')
            workload = best.get('workload', 'N/A')
            throughput = best.get('throughput_work_per_sec', 0)
            story.append(Paragraph(
                f"<b>Best Performance:</b> {instance_type} running {workload} "
                f"achieved {throughput:.2f} work units/second.",
                self.styles['Normal']
            ))
        
        if metrics.get("best_efficiency") is not None:
            best_eff = metrics["best_efficiency"]
            instance_type = best_eff.get('instance_type', 'N/A')
            workload = best_eff.get('workload', 'N/A')
            efficiency = best_eff.get('efficiency_joules_per_work', 0)
            story.append(Paragraph(
                f"<b>Most Energy Efficient:</b> {instance_type} running {workload} "
                f"consumed only {efficiency:.6f} Joules per work unit.",
                self.styles['Normal']
            ))
        
        story.append(PageBreak())
        
        # Test Methodology
        story.append(Paragraph("Test Methodology", self.styles['SectionHeader']))
        
        story.append(Paragraph("<b>Overview</b>", self.styles['SubsectionHeader']))
        story.append(Paragraph(
            "The benchmark suite tests four blockchain consensus algorithms across four EC2 instance types, "
            "measuring performance (throughput) and energy efficiency (energy per work unit).",
            self.styles['BodyText']
        ))
        
        story.append(Paragraph("<b>Instance Types Tested</b>", self.styles['SubsectionHeader']))
        story.append(Paragraph(
            "• <b>t4g.micro</b> (ARM): 2 vCPU, 1GB RAM - Burstable performance instance<br/>"
            "• <b>t3.micro</b> (x86): 2 vCPU, 1GB RAM - Burstable performance instance<br/>"
            "• <b>g4dn.xlarge</b> (GPU): 4 vCPU, 16GB RAM, NVIDIA T4 GPU<br/>"
            "• <b>f1.2xlarge</b> (FPGA): 8 vCPU, 122GB RAM, Xilinx Virtex UltraScale+ VU9P",
            self.styles['BodyText']
        ))
        
        story.append(Paragraph("<b>Workloads Tested</b>", self.styles['SubsectionHeader']))
        story.append(Paragraph(
            "• <b>Proof of Work (PoW)</b>: SHA-256 mining with fixed difficulty target<br/>"
            "• <b>Proof of Stake (PoS)</b>: Ed25519 signature verification<br/>"
            "• <b>Byzantine Fault Tolerance (BFT)</b>: PBFT consensus simulation (4 nodes, 1 Byzantine tolerance)<br/>"
            "• <b>Zero-Knowledge Proofs (ZK)</b>: ZK-SNARK proof generation simulation",
            self.styles['BodyText']
        ))
        
        story.append(Paragraph("<b>Measurement Protocol</b>", self.styles['SubsectionHeader']))
        story.append(Paragraph(
            "Each benchmark follows a standardized protocol to ensure comparability:<br/>"
            "• <b>Warmup Period:</b> 30 seconds (excluded from results)<br/>"
            "• <b>Measurement Period:</b> 5 minutes (300 seconds) - only this period counts<br/>"
            "• <b>Fixed Parameters:</b> Same difficulty targets, key sizes, and workload configurations across all instances<br/>"
            "• <b>Fresh Instances:</b> Each test uses a freshly provisioned instance to avoid caching effects<br/>"
            "• <b>Real-time Monitoring:</b> CloudWatch metrics collected at 1-minute intervals",
            self.styles['BodyText']
        ))
        
        story.append(Paragraph("<b>Performance Measurement</b>", self.styles['SubsectionHeader']))
        story.append(Paragraph(
            "Performance is measured as <b>throughput</b>: the number of work units completed per second. "
            "Each workload counts distinct work units:<br/>"
            "• PoW: SHA-256 hash attempts<br/>"
            "• PoS: Ed25519 signature verifications<br/>"
            "• BFT: Consensus rounds completed<br/>"
            "• ZK: Proof generations completed",
            self.styles['BodyText']
        ))
        
        story.append(Paragraph("<b>Energy Efficiency Measurement</b>", self.styles['SubsectionHeader']))
        story.append(Paragraph(
            "Energy consumption is estimated using a power-based model:<br/>"
            "• <b>Base Power:</b> AWS published TDP (Thermal Design Power) values<br/>"
            "• <b>CPU Power:</b> Base TDP × (CPU Utilization / 100)<br/>"
            "• <b>GPU Power:</b> Measured directly from nvidia-smi for GPU instances<br/>"
            "• <b>Energy:</b> Power (Watts) × Time (seconds) = Energy (Joules)<br/>"
            "• <b>Efficiency:</b> Energy (Joules) / Work Units = Joules per work unit<br/>"
            "<i>Note: Lower efficiency values indicate better energy efficiency.</i>",
            self.styles['BodyText']
        ))
        
        story.append(PageBreak())
        
        # Results Summary
        if df is not None and not df.empty:
            story.append(Paragraph("Results Summary", self.styles['SectionHeader']))
            
            # Summary table
            summary_cols = ["instance_type", "workload", "work_units_completed", 
                          "throughput_work_per_sec", "efficiency_joules_per_work", 
                          "cost_per_work_usd", "average_cpu_percent"]
            summary_df = df[summary_cols].copy()
            summary_table = self.format_table(summary_df)
            story.append(summary_table)
            story.append(Spacer(1, 0.3*inch))
            
            story.append(PageBreak())
            
            # Performance Analysis
            story.append(Paragraph("Performance Analysis", self.styles['SectionHeader']))
            
            for workload in df["workload"].unique():
                story.append(Paragraph(f"{workload.upper()} Workload", self.styles['SubsectionHeader']))
                workload_df = df[df["workload"] == workload].sort_values("throughput_work_per_sec", ascending=False)
                
                if not workload_df.empty:
                    # Performance table
                    perf_cols = ["instance_type", "throughput_work_per_sec", "throughput_per_vcpu", 
                                "work_units_completed", "measurement_duration_seconds"]
                    perf_table = self.format_table(workload_df[perf_cols])
                    story.append(perf_table)
                    story.append(Spacer(1, 0.2*inch))
                    
                    # Analysis
                    best = workload_df.iloc[0]
                    story.append(Paragraph(
                        f"The <b>{best['instance_type']}</b> instance achieved the highest throughput "
                        f"of {float(best.get('throughput_work_per_sec', 0)):.2f} work units/second for {workload} workloads, "
                        f"completing {int(best.get('work_units_completed', 0))} work units in {int(best.get('measurement_duration_seconds', 0))} seconds.",
                        self.styles['BodyText']
                    ))
                    story.append(Spacer(1, 0.1*inch))
                    
                    # Performance graph
                    perf_graph = temp_dir / f"perf_{workload}.png"
                    if perf_graph.exists():
                        img = Image(str(perf_graph), width=6*inch, height=3.75*inch)
                        story.append(img)
                        story.append(Spacer(1, 0.2*inch))
            
            story.append(PageBreak())
            
            # Energy Efficiency Analysis
            story.append(Paragraph("Energy Efficiency Analysis", self.styles['SectionHeader']))
            
            for workload in df["workload"].unique():
                story.append(Paragraph(f"{workload.upper()} Workload", self.styles['SubsectionHeader']))
                workload_df = df[df["workload"] == workload]
                eff_df = workload_df[workload_df["efficiency_joules_per_work"] != float('inf')].sort_values("efficiency_joules_per_work", ascending=True)
                
                if not eff_df.empty:
                    # Efficiency table
                    eff_cols = ["instance_type", "efficiency_joules_per_work", "energy_joules", 
                               "work_units_completed", "average_cpu_percent"]
                    eff_table = self.format_table(eff_df[eff_cols])
                    story.append(eff_table)
                    story.append(Spacer(1, 0.2*inch))
                    
                    # Analysis
                    best_eff = eff_df.iloc[0]
                    story.append(Paragraph(
                        f"The <b>{best_eff['instance_type']}</b> instance was the most energy-efficient, "
                        f"consuming only {best_eff['efficiency_joules_per_work']:.6f} Joules per work unit. "
                        f"Total energy consumption was {float(best_eff.get('energy_joules', 0)):.2f} Joules for "
                        f"{int(best_eff.get('work_units_completed', 0))} work units.",
                        self.styles['BodyText']
                    ))
                    story.append(Spacer(1, 0.1*inch))
                    
                    # Efficiency graph
                    eff_graph = temp_dir / f"eff_{workload}.png"
                    if eff_graph.exists():
                        img = Image(str(eff_graph), width=6*inch, height=3.75*inch)
                        story.append(img)
                        story.append(Spacer(1, 0.2*inch))
            
            story.append(PageBreak())
        
        # Detailed Results (Verbose Logs)
        story.append(Paragraph("Detailed Results and Verbose Logs", self.styles['SectionHeader']))
        
        raw_results = results.get("raw_results", [])
        if raw_results:
            story.append(Paragraph(
                f"This section contains detailed logs from {len(raw_results)} benchmark runs.",
                self.styles['BodyText']
            ))
            story.append(Spacer(1, 0.2*inch))
            
            for i, result in enumerate(raw_results, 1):
                story.append(Paragraph(
                    f"Benchmark {i}: {result.get('instance_type', 'Unknown')} / {result.get('workload', 'Unknown')}",
                    self.styles['SubsectionHeader']
                ))
                
                # Instance info
                story.append(Paragraph(f"<b>Instance ID:</b> {result.get('instance_id', 'N/A')}", self.styles['Normal']))
                story.append(Paragraph(f"<b>Public IP:</b> {result.get('public_ip', 'N/A')}", self.styles['Normal']))
                story.append(Paragraph(f"<b>Measurement Start:</b> {result.get('measurement_start', 'N/A')}", self.styles['Normal']))
                story.append(Paragraph(f"<b>Duration:</b> {result.get('measurement_duration_seconds', 'N/A')} seconds", self.styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
                
                # Workload output summary
                workload_output = result.get("workload_output", {})
                story.append(Paragraph("<b>Workload Output:</b>", self.styles['Normal']))
                # Safely format numeric values
                throughput = result.get('throughput_work_per_sec', 0)
                energy = result.get('energy_joules', 0)
                efficiency = result.get('efficiency_joules_per_work', float('inf'))
                try:
                    throughput_str = f"{float(throughput):.2f}" if throughput not in ['N/A', None] else 'N/A'
                    energy_str = f"{float(energy):.2f}" if energy not in ['N/A', None] else 'N/A'
                    if efficiency == float('inf') or efficiency == 'inf' or efficiency in ['N/A', None]:
                        efficiency_str = 'N/A'
                    else:
                        efficiency_str = f"{float(efficiency):.6f}"
                except (ValueError, TypeError):
                    throughput_str = str(throughput)
                    energy_str = str(energy)
                    efficiency_str = str(efficiency)
                
                story.append(Paragraph(
                    f"• Work units completed: {workload_output.get('total_count', 'N/A')}<br/>"
                    f"• Throughput: {throughput_str} work/sec<br/>"
                    f"• Energy consumed: {energy_str} Joules<br/>"
                    f"• Efficiency: {efficiency_str} Joules/work",
                    self.styles['Normal']
                ))
                story.append(Spacer(1, 0.1*inch))
                
                # Metrics summary
                metrics = result.get("metrics", {})
                if metrics:
                    story.append(Paragraph("<b>Resource Metrics:</b>", self.styles['Normal']))
                    # Safely format numeric values
                    try:
                        avg_cpu = float(metrics.get('average_cpu_percent', 0)) if metrics.get('average_cpu_percent') not in ['N/A', None] else 0
                        max_cpu = float(metrics.get('max_cpu_percent', 0)) if metrics.get('max_cpu_percent') not in ['N/A', None] else 0
                        mem_usage = float(metrics.get('memory_usage_percent', 0)) if metrics.get('memory_usage_percent') not in ['N/A', None] else 0
                        gpu_percent = float(metrics.get('average_gpu_percent', 0)) if metrics.get('average_gpu_percent') not in ['N/A', None] else 0
                        gpu_power = float(metrics.get('average_gpu_power_watts', 0)) if metrics.get('average_gpu_power_watts') not in ['N/A', None] else 0
                        
                        cpu_str = f"{avg_cpu:.1f}" if avg_cpu > 0 else "N/A"
                        max_cpu_str = f"{max_cpu:.1f}" if max_cpu > 0 else "N/A"
                        mem_str = f"{mem_usage:.1f}" if mem_usage > 0 else "N/A"
                        gpu_percent_str = f"{gpu_percent:.1f}" if gpu_percent > 0 else "N/A"
                        gpu_power_str = f"{gpu_power:.1f}" if gpu_power > 0 else "N/A"
                    except (ValueError, TypeError):
                        cpu_str = str(metrics.get('average_cpu_percent', 'N/A'))
                        max_cpu_str = str(metrics.get('max_cpu_percent', 'N/A'))
                        mem_str = str(metrics.get('memory_usage_percent', 'N/A'))
                        gpu_percent_str = str(metrics.get('average_gpu_percent', 'N/A') or 'N/A')
                        gpu_power_str = str(metrics.get('average_gpu_power_watts', 'N/A') or 'N/A')
                    
                    story.append(Paragraph(
                        f"• Average CPU: {cpu_str}%<br/>"
                        f"• Max CPU: {max_cpu_str}%<br/>"
                        f"• Memory Usage: {mem_str}%<br/>"
                        f"• GPU Utilization: {gpu_percent_str}%<br/>"
                        f"• GPU Power: {gpu_power_str}W",
                        self.styles['Normal']
                    ))
                    story.append(Spacer(1, 0.2*inch))
        else:
            story.append(Paragraph("No detailed results available.", self.styles['Normal']))
        
        story.append(PageBreak())
        
        # Conclusion and Recommendations
        story.append(Paragraph("Conclusions and Recommendations", self.styles['SectionHeader']))
        
        if df is not None and not df.empty:
            story.append(Paragraph("<b>Key Findings</b>", self.styles['SubsectionHeader']))
            
            # Workload-specific recommendations
            for workload in df["workload"].unique():
                workload_df = df[df["workload"] == workload]
                if workload_df.empty:
                    continue
                
                best_perf_row = workload_df.loc[workload_df["throughput_work_per_sec"].idxmax()]
                best_perf = best_perf_row.to_dict() if isinstance(best_perf_row, pd.Series) else best_perf_row
                eff_df = workload_df[workload_df["efficiency_joules_per_work"] != float('inf')]
                best_eff_row = eff_df.loc[eff_df["efficiency_joules_per_work"].idxmin()] if not eff_df.empty else None
                best_eff = best_eff_row.to_dict() if best_eff_row is not None and isinstance(best_eff_row, pd.Series) else best_eff_row
                
                story.append(Paragraph(f"<b>{workload.upper()} Workload:</b>", self.styles['Normal']))
                
                perf_throughput = best_perf.get('throughput_work_per_sec', 0)
                perf_throughput_str = f"{float(perf_throughput):.2f}" if perf_throughput not in ['N/A', None] else 'N/A'
                perf_instance = best_perf.get('instance_type', 'N/A')
                
                if best_eff is not None and perf_instance != best_eff.get('instance_type'):
                    eff_value = best_eff.get('efficiency_joules_per_work', float('inf'))
                    eff_str = f"{float(eff_value):.6f}" if eff_value != float('inf') and eff_value not in ['N/A', None] else 'N/A'
                    eff_instance = best_eff.get('instance_type', 'N/A')
                    story.append(Paragraph(
                        f"For maximum performance, use <b>{perf_instance}</b> "
                        f"({perf_throughput_str} work/sec). "
                        f"For optimal energy efficiency, use <b>{eff_instance}</b> "
                        f"({eff_str} J/work).",
                        self.styles['Normal']
                    ))
                else:
                    eff_value = best_eff.get('efficiency_joules_per_work', float('inf')) if best_eff else float('inf')
                    eff_str = f"{float(eff_value):.6f}" if eff_value != float('inf') and eff_value not in ['N/A', None] else 'N/A'
                    story.append(Paragraph(
                        f"<b>{perf_instance}</b> provides both the best performance "
                        f"({perf_throughput_str} work/sec) and energy efficiency "
                        f"({eff_str} J/work if available) for {workload} workloads.",
                        self.styles['Normal']
                    ))
                story.append(Spacer(1, 0.1*inch))
            
            story.append(Paragraph("<b>Trade-offs</b>", self.styles['SubsectionHeader']))
            story.append(Paragraph(
                "Higher-performance instances typically consume more energy. The choice between instance types "
                "depends on priorities:<br/>"
                "• <b>Performance-critical:</b> Choose instances with highest throughput<br/>"
                "• <b>Energy-constrained:</b> Choose instances with lowest Joules/work<br/>"
                "• <b>Cost-optimized:</b> Balance performance and cost per work unit<br/>"
                "• <b>Balanced:</b> Consider throughput per vCPU and efficiency per vCPU for normalized comparison",
                self.styles['BodyText']
            ))
        
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                             self.styles['BodyText']))
        
        # Build PDF
        doc.build(story)
        
        # Cleanup temp directory
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        
        print(f"PDF report generated: {output_path}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate benchmark PDF report")
    parser.add_argument("--results", default="results", help="Results directory")
    parser.add_argument("--output", default="results/benchmark_report.pdf", help="Output PDF path")
    
    args = parser.parse_args()
    
    generator = BenchmarkReportGenerator(args.results)
    generator.generate_report(args.output)

