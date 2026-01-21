#!/usr/bin/env python3

import os
import sys
import argparse
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re


def load_integrated_data(csv_files: List[str]) -> Dict[str, pd.DataFrame]:
    """
    Load integrated CSV files and return a dictionary mapping variant names to DataFrames.
    
    Args:
        csv_files: List of CSV file paths to load
    
    Returns:
        Dictionary mapping variant names (extracted from filename) to DataFrames
    """
    integrated_dfs = {}
    
    for csv_file in csv_files:
        csv_path = Path(csv_file)
        
        if not csv_path.exists():
            print(f"Warning: File not found: {csv_file}")
            continue
        
        if not csv_path.suffix == '.csv':
            print(f"Warning: Not a CSV file: {csv_file}")
            continue
        
        try:
            # Extract variant name from filename
            # Filename format: integrated_<variant_name>.csv
            filename = csv_path.name
            if filename.startswith('integrated_') and filename.endswith('.csv'):
                variant_name = filename[11:-4]  # Remove 'integrated_' prefix and '.csv' suffix
            else:
                variant_name = csv_path.stem  # Use filename without extension as fallback
            
            # Load CSV file
            df = pd.read_csv(csv_file, dtype={'timestamp_ns': 'int64'})
            
            integrated_dfs[variant_name] = df
            print(f"Loaded {len(df)} rows from {csv_file}")
            
        except Exception as e:
            print(f"Error loading {csv_file}: {e}")
    
    return integrated_dfs
    


def parse_variant_params(variant_name):
    """Extract swaprate goal and cold threshold from variant name"""
    # Example: my_prcl_swaprate_10_cold_500ms or my_prcl_rss_409600_cold_500ms
    swaprate_match = re.search(r'swaprate_(\d+)', variant_name)
    cold_match = re.search(r'cold_([^_]+)', variant_name)
    
    swaprate = swaprate_match.group(1) if swaprate_match else "unknown"
    cold = cold_match.group(1) if cold_match else "unknown"
    
    return swaprate, cold


def analyze_data(integrated_dfs: Dict[str, pd.DataFrame], output_dir: Path):
    """Analyze and visualize data from integrated DataFrames with lag analysis."""
    print("\n=== Starting Analysis ===")
    
    # Create output directories
    lag_analysis_dir = output_dir / "lag_analysis"
    lag_analysis_dir.mkdir(exist_ok=True)
    
    scatter_plots_dir = output_dir / "scatter_plots"
    scatter_plots_dir.mkdir(exist_ok=True)
    
    max_lag = 50  # 50 * 100ms = 5 seconds
    
    for variant_name, df in integrated_dfs.items():
        if df is None or df.empty:
            continue
            
        print(f"\n--- Processing {variant_name} ---")
        
        # Find relevant columns
        swaprate_cols = [col for col in df.columns if 'swaprate_bp' in col.lower()]
        majflt_cols = [col for col in df.columns if 'majflt' in col.lower() or 'pgmajfaults' in col.lower()]
        psi_cols = [col for col in df.columns if 'psi' in col.lower() and 'some' in col.lower() and 'increment' in col.lower()]
        
        if not swaprate_cols:
            print(f"  Warning: No swaprate column found")
            continue
            
        swaprate_col = swaprate_cols[0]
        majflt_col = majflt_cols[0] if majflt_cols else None
        psi_col = psi_cols[0] if psi_cols else None
        
        # --- Analyze MAJFLT ---
        if majflt_col:
            print(f"  Analyzing MAJFLT (SwapRate vs MAJFLT)...")
            # 1. Calculate Lag Correlation
            lags, corrs = calculate_lagged_correlation(df[swaprate_col], df[majflt_col], max_lag)
            plot_lag_correlation(lags, corrs, variant_name, "SwapRate", "MAJFLT", lag_analysis_dir)
            
            # 2. Find Best Lag
            best_lag, max_corr = find_best_lag(lags, corrs)
            print(f"    Best Lag: {best_lag} (Corr: {max_corr:.3f})")
            
            # 3. Prepare Lag-Adjusted Data
            # Shift MAJFLT by -best_lag to align with SwapRate
            y_shifted = df[majflt_col].shift(-best_lag)
            
            # Create temp df for filtering
            plot_df = pd.DataFrame({
                'x': df[swaprate_col],
                'y': y_shifted
            }).dropna()
            
            # We now include zeros as requested
            print(f"    Plotting {len(plot_df)} points (Including zeros)")
            
            if not plot_df.empty:
                # 4. Plot Scatter
                safe_name = variant_name.replace('/', '_').replace(' ', '_')
                output_path = scatter_plots_dir / f"scatter_{safe_name}_majflt_lag{best_lag}.png"
                title = f"{variant_name}\nMAJFLT vs SwapRate (Lag: {best_lag}00ms, Corr: {max_corr:.3f})"
                
                create_single_variant_plot(
                    plot_df['x'], plot_df['y'], 
                    output_path, 
                    title, 
                    xlabel='Swap Rate (VmSwap/(RSS+VmSwap))',
                    ylabel='MAJFLT Count (Lag Adjusted)'
                )
        
        # --- Analyze PSI ---
        if psi_col:
            print(f"  Analyzing PSI (SwapRate vs PSI)...")
            # 1. Calculate Lag Correlation
            lags, corrs = calculate_lagged_correlation(df[swaprate_col], df[psi_col], max_lag)
            plot_lag_correlation(lags, corrs, variant_name, "SwapRate", "PSI", lag_analysis_dir)
            
            # 2. Find Best Lag
            best_lag, max_corr = find_best_lag(lags, corrs)
            print(f"    Best Lag: {best_lag} (Corr: {max_corr:.3f})")
            
            # 3. Prepare Lag-Adjusted Data
            y_shifted = df[psi_col].shift(-best_lag)
            
            plot_df = pd.DataFrame({
                'x': df[swaprate_col],
                'y': y_shifted
            }).dropna()
            
            # We now include zeros as requested
            print(f"    Plotting {len(plot_df)} points (Including zeros)")
            
            if not plot_df.empty:
                # 4. Plot Scatter
                safe_name = variant_name.replace('/', '_').replace(' ', '_')
                output_path = scatter_plots_dir / f"scatter_{safe_name}_psi_lag{best_lag}.png"
                title = f"{variant_name}\nPSI vs SwapRate (Lag: {best_lag}00ms, Corr: {max_corr:.3f})"
                
                create_single_variant_plot(
                    plot_df['x'], plot_df['y'], 
                    output_path, 
                    title, 
                    xlabel='Swap Rate (VmSwap/(RSS+VmSwap))',
                    ylabel='PSI Some Increment (ns) (Lag Adjusted)'
                )

    print(f"\n=== Analysis Complete ===")


def find_best_lag(lags, corrs):
    """Find the lag with the maximum correlation."""
    valid_indices = [i for i, c in enumerate(corrs) if not np.isnan(c)]
    if not valid_indices:
        return 0, 0.0
    
    max_idx = np.nanargmax(corrs)
    return lags[max_idx], corrs[max_idx]


def create_single_variant_plot(x_data, y_data, output_path, title, xlabel, ylabel):
    """Create a scatter plot for a single variant."""
    plt.figure(figsize=(12, 8))
    
    # Scatter - optimized for dense data
    plt.scatter(x_data, y_data, alpha=0.6, s=30, edgecolors='none', color='#2ca02c')
    
    # Trend line
    if len(x_data) > 3:
        try:
            coeffs = np.polyfit(x_data, y_data, 1)
            trend_line = np.poly1d(coeffs)
            x_trend = np.linspace(x_data.min(), x_data.max(), 100)
            plt.plot(x_trend, trend_line(x_trend), '--', color='red', linewidth=2, label='Trend')
            plt.legend()
        except Exception:
            pass
            
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    
    # Add stats
    plt.figtext(0.02, 0.02, f'Points: {len(x_data):,}', 
               fontsize=10, ha='left', va='bottom',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
               
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"    Saved plot: {output_path.name}")


def calculate_lagged_correlation(series1, series2, max_lag=50):
    """
    Calculate cross-correlation between series1 and series2 at different lags.
    Lag k: Correlation(series1(t), series2(t+k))
    Only considers positive lags (series1 leads series2).
    """
    # Only analyze positive lags (0 to max_lag)
    # Lag 0: Simultaneous
    # Lag > 0: series1(t) vs series2(t+lag) -> series1 leads
    lags = np.arange(0, max_lag + 1)
    corrs = []
    for lag in lags:
        # shift(-lag) brings future values (if lag>0) to current index
        s2_shifted = series2.shift(-lag)
        # pandas corr ignores NaNs
        corr = series1.corr(s2_shifted)
        corrs.append(corr)
    return lags, corrs


def plot_lag_correlation(lags, corrs, variant_name, var1_name, var2_name, output_dir):
    """Plot lag correlation results."""
    plt.figure(figsize=(10, 6))
    plt.plot(lags, corrs, marker='o', markersize=3)
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    
    # Find max correlation
    valid_corrs = [c for c in corrs if not np.isnan(c)]
    if valid_corrs:
        max_corr = np.nanmax(corrs)
        max_lag = lags[np.nanargmax(corrs)]
        
        plt.annotate(f'Max Corr: {max_corr:.3f} @ Lag {max_lag}', 
                     xy=(max_lag, max_corr), xytext=(10, 10), textcoords='offset points',
                     arrowprops=dict(arrowstyle='->'),
                     bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5))
    
    plt.title(f'Lag Correlation: {var1_name} vs {var2_name}\n{variant_name}')
    plt.xlabel(f'Lag (steps of 100ms)\n{var1_name} leads (Cause) -> {var2_name} (Effect)')
    plt.ylabel('Correlation Coefficient')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    safe_name = variant_name.replace('/', '_').replace(' ', '_')
    filename = f"lag_corr_{safe_name}_{var1_name}_vs_{var2_name}.png"
    plt.savefig(output_dir / filename, dpi=150)
    plt.close()


def create_plot(plot_data, output_path, title=None, ylabel='MAJFLT Count', xlabel=None):
    """Create count vs swaprate relationship plot from integrated data"""
    if not plot_data:
        print("No plot data provided")
        return
    
    # Default xlabel if not provided
    if xlabel is None:
        xlabel = 'Swap Rate (VmSwap/(RSS+VmSwap))'
    
    # Create the plot
    plt.figure(figsize=(12, 8))
    
    # Generate distinct colors for different directories
    colors = plt.cm.Set1(np.linspace(0, 1, max(len(plot_data), 10)))
    
    for i, data_info in enumerate(plot_data):
        color = colors[i % len(colors)]
        
        # Create scatter plot
        plt.scatter(data_info['x_data'], data_info['y_data'], 
                   alpha=0.7, label=data_info['source'], color=color, 
                   s=30, edgecolors='black', linewidth=0.5)
        
        # Add trend line if we have enough points
        if len(data_info['x_data']) > 3:
            try:
                # Fit linear regression
                coeffs = np.polyfit(data_info['x_data'], data_info['y_data'], 1)
                trend_line = np.poly1d(coeffs)
                x_trend = np.linspace(data_info['x_data'].min(), data_info['x_data'].max(), 100)
                plt.plot(x_trend, trend_line(x_trend), '--', alpha=0.8, color=color, linewidth=2)
            except Exception:
                pass  # Skip trend line if fitting fails
        
        print(f"  Plotted {data_info['points']} points for {data_info['source']}")
    
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title if title else f'{ylabel} vs Swap Rate')
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Add statistics annotation
    if len(plot_data) > 1:
        total_points = sum(data['points'] for data in plot_data)
        plt.figtext(0.02, 0.02, f'Total data points: {total_points:,}', 
                   fontsize=10, ha='left', va='bottom',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved plot: {output_path}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description='Analyze DAMON data from integrated CSV files'
    )
    parser.add_argument('output_dir', help='Output directory path for analysis results')
    parser.add_argument('input_files', nargs='+', help='Integrated CSV file paths to analyze')
    
    args = parser.parse_args()
    
    # Validate output directory
    output_dir = Path(args.output_dir)
    print(f"Output directory: {output_dir.absolute()}")
    
    if not output_dir.exists():
        print(f"Output directory does not exist, creating: {output_dir.absolute()}")
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Validate input files
    input_files = []
    for input_file in args.input_files:
        file_path = Path(input_file)
        if file_path.exists() and file_path.is_file() and file_path.suffix == '.csv':
            input_files.append(str(file_path.absolute()))
        else:
            print(f"Warning: Invalid input file: {input_file}")
    
    if not input_files:
        print("Error: No valid input CSV files found")
        return
    
    print(f"Found {len(input_files)} valid input files")
    
    # Load integrated data
    integrated_dfs = load_integrated_data(input_files)
    
    if not integrated_dfs:
        print("Error: No data loaded from input files")
        return
    
    # Analyze and visualize data
    analyze_data(integrated_dfs, output_dir)
    
    # Save metadata
    metadata = {
        'input_files': input_files,
        'output_directory': str(output_dir.absolute()),
        'loaded_variants': list(integrated_dfs.keys()),
        'data_summary': {
            'total_variants': len(integrated_dfs),
            'variant_shapes': {
                variant: list(df.shape) 
                for variant, df in integrated_dfs.items()
            }
        }
    }
    
    metadata_file = output_dir / "analysis_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    
    print(f"\nAnalysis complete!")
    print(f"Metadata saved to: {metadata_file}")


if __name__ == "__main__":
    main()
