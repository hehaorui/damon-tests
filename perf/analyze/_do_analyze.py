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

def find_csv_files(directory):
    """Find CSV files directly in the specified directory (no subdirectories)"""
    csv_files = {}
    
    if not os.path.exists(directory):
        print(f"Error: Directory does not exist: {directory}")
        return csv_files
    
    if not os.path.isdir(directory):
        print(f"Error: Path is not a directory: {directory}")
        return csv_files
    
    try:
        for file in os.listdir(directory):
            if file.endswith('.csv'):
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path):  # Ensure it's a file, not a directory
                    csv_files[file] = file_path
    except Exception as e:
        print(f"Error listing directory {directory}: {e}")
    
    return csv_files

def process_csv(csv_file_path):
    """Process a single CSV file and return its structure and data"""
    if not os.path.exists(csv_file_path):
        print(f"Error: File does not exist: {csv_file_path}")
        return None, None
        
    if not csv_file_path.endswith('.csv'):
        print(f"Error: File is not a CSV: {csv_file_path}")
        return None, None
    
    filename = os.path.basename(csv_file_path)
    
    # Analyze file structure
    structure = analyze_structure(csv_file_path)
    if not structure:
        print(f"Error: Could not analyze structure of {csv_file_path}")
        return None, None
    
    print(f"  {filename}: {structure['type']}")
    
    # Load data based on file type
    if structure['type'] == 'damon_data':
        df = load_damon(csv_file_path)
        if df is not None:
            return {filename: df}, {filename: structure}
    elif structure['type'] == 'timestamped_metrics':
        df = load_timestamped(csv_file_path)
        if df is not None:
            return {filename: df}, {filename: structure}
    else:
        print(f"Warning: Unknown CSV file type for {filename}, attempting to load as timestamped data")
        # Try to load as timestamped CSV for unknown CSV files
        df = load_timestamped(csv_file_path)
        if df is not None:
            return {filename: df}, {filename: structure}
        else:
            return {filename: None}, {filename: structure}
    
    return None, None

def read_csv_sample(file_path, max_rows=5):
    """Read sample of CSV file to understand structure"""
    try:
        with open(file_path, 'r') as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_rows:
                    break
                lines.append(line.strip())
        return lines
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def analyze_structure(file_path):
    """Analyze CSV file structure and return metadata"""
    sample = read_csv_sample(file_path, 3)
    if not sample:
        return None
    
    first_line = sample[0] if sample else ""
    second_line = sample[1] if len(sample) > 1 else ""
    
    # Parse header
    headers = first_line.split(',') if first_line else []
    
    # Determine file type based on headers and filename
    filename = os.path.basename(file_path)
    
    if filename == 'damon_data.csv':
        return {
            'type': 'damon_data',
            'time_columns': ['start_time_ns', 'end_time_ns'],
            'headers': headers,
            'sample_row': second_line
        }
    elif 'timestamp_ns' in headers[0].lower():
        return {
            'type': 'timestamped_metrics',
            'time_column': 'timestamp_ns',
            'headers': headers,
            'sample_row': second_line
        }
    else:
        return {
            'type': 'unknown_csv',
            'headers': headers,
            'sample_row': second_line
        }

def load_damon(csv_path):
    """Load damon_data.csv with proper parsing"""
    try:
        # Read in chunks to avoid memory issues
        df = pd.read_csv(csv_path, dtype={'start_time_ns': 'int64', 'end_time_ns': 'int64'})
        
        # Use end time for alignment
        df['timestamp_ns'] = df['end_time_ns']
        
        return df
    except Exception as e:
        print(f"Error loading damon_data.csv: {e}")
        return None

def load_timestamped(csv_path):
    """Load timestamped CSV files"""
    try:
        df = pd.read_csv(csv_path, dtype={'timestamp_ns': 'int64'})
        return df
    except Exception as e:
        print(f"Error loading {csv_path}: {e}")
        return None


def parse_variant_params(variant_name):
    """Extract rss and cold threshold from variant name"""
    # Example: my_prcl_rss_409600_cold_500ms
    rss_match = re.search(r'rss_(\d+)', variant_name)
    cold_match = re.search(r'cold_([^_]+)', variant_name)
    
    rss = rss_match.group(1) if rss_match else "unknown"
    cold = cold_match.group(1) if cold_match else "unknown"
    
    return rss, cold

def create_plot(plot_data, output_path, title=None, ylabel='MAJFLT Count'):
    """Create count vs RSS/VSZ ratio relationship plot from integrated data"""
    if not plot_data:
        print("No plot data provided")
        return
    
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
    
    plt.xlabel('RSS/VSZ Ratio')
    plt.ylabel(ylabel)
    plt.title(title if title else f'{ylabel} vs RSS/VSZ Ratio')
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



def integrate_data(dataframes: Dict[str, pd.DataFrame]):
    """
    Integrate multiple dataframes by resampling to a common frequency.
    Handles inconsistent sampling frequencies and uneven periods using pandas reindexing.
    """
    if not dataframes:
        return None
    
    print("Integrating data using pandas resampling...")
    
    # 1. Preprocess: Convert timestamps to datetime and collect stats
    processed_dfs = {}
    all_timestamps = []
    intervals = []
    
    for name, df in dataframes.items():
        if df.empty:
            continue
        
        # Work on a copy
        df = df.copy()
        
        # Normalize timestamp column
        if 'end_time_ns' in df.columns and 'timestamp_ns' not in df.columns:
            df = df.rename(columns={'end_time_ns': 'timestamp_ns'})
        
        # Deduplicate columns if needed
        if df.columns.duplicated().any():
            df = df.loc[:, ~df.columns.duplicated().keep('first')]
            
        if 'timestamp_ns' not in df.columns:
            print(f"Warning: {name} has no timestamp column")
            continue
            
        # Ensure timestamp_ns is a Series
        if isinstance(df['timestamp_ns'], pd.DataFrame):
            print(f"Warning: {name} still has duplicate timestamp_ns columns after deduplication, fixing...")
            df['timestamp_ns'] = df['timestamp_ns'].iloc[:, 0]
            
        # Use timestamp_ns as index (numeric)
        # We avoid to_datetime to prevent issues and overhead, working directly with ns
        try:
            df = df.set_index('timestamp_ns').sort_index()
        except Exception as e:
            print(f"Error setting index for {name}: {e}")
            continue

            
        processed_dfs[name] = df
        
        # Collect stats for frequency determination
        if len(df) > 1:
            # Calculate median interval
            diffs = df.index.to_series().diff().dropna()
            median_diff = diffs.median()
            if median_diff > 0:
                intervals.append(median_diff)
            
        all_timestamps.extend(df.index)

    if not processed_dfs:
        return None

    # 2. Determine common time grid
    # Fixed 100ms grid to ensure consistent high-frequency sampling
    target_step = 100_000_000  # 100ms in nanoseconds
        
    print(f"Target sampling step: {target_step} ns (fixed 100ms grid)")
    
    # Define global time range
    # Use INTERSECTION of time ranges to avoid NaNs at edges
    # (Latest start time to Earliest end time)
    start_times = [df.index.min() for df in processed_dfs.values()]
    end_times = [df.index.max() for df in processed_dfs.values()]
    
    if not start_times or not end_times:
        return None
        
    min_time = max(start_times) # Latest start
    max_time = min(end_times)   # Earliest end
    
    print(f"Time overlap range: {min_time} to {max_time}")
    
    if min_time > max_time:
        print("Error: No time overlap found between datasets")
        return None
    
    # Create regular numeric index
    # Use numpy arange for numeric grid
    common_index = pd.Index(np.arange(min_time, max_time + target_step, target_step), name='timestamp_ns')
    print(f"Created common time grid: {len(common_index)} points")
    
    # 3. Resample and Merge
    aligned_dfs = []
    
    # Tolerance for matching: use a reasonable window (e.g., 2x step)
    tolerance = target_step * 2
    print(f"Using alignment tolerance: {tolerance} ns")

    for name, df in processed_dfs.items():
        # Rename columns to avoid conflicts
        cols = {c: f"{name}_{c}" for c in df.columns}
        df_renamed = df.rename(columns=cols)
        
        # Reindex to common grid
        # method='nearest' finds the closest valid timestamp within tolerance
        try:
            df_aligned = df_renamed.reindex(common_index, method='nearest', tolerance=tolerance)
            aligned_dfs.append(df_aligned)
        except Exception as e:
            print(f"Error reindexing {name}: {e}")
        
    if not aligned_dfs:
        return None

    # Concatenate all aligned dataframes
    integrated_df = pd.concat(aligned_dfs, axis=1)
    
    # Clean up result
    integrated_df = integrated_df.reset_index()
    
    # Sort by timestamp
    integrated_df = integrated_df.sort_values('timestamp_ns')
    
    return integrated_df

def process_directory(directory):
    """Process CSV files in a single directory and return integrated data"""
    print(f"\n=== Processing Directory: {directory} ===")
    
    csv_files = find_csv_files(directory)
    print(f"Found {len(csv_files)} CSV files")
    
    if not csv_files:
        print("No CSV files found in directory")
        return {}, {}
    
    all_dataframes = {}
    all_structures = {}
    
    for filename, filepath in csv_files.items():
        print(f"\n--- Processing: {filepath} ---")
        
        dataframes, structures = process_csv(filepath)
        
        if dataframes:
            for key, value in dataframes.items():
                if value is not None:  # Only add non-None dataframes
                    all_dataframes[key] = value
                    if isinstance(value, pd.DataFrame):
                        print(f"  Loaded {key}: {len(value)} rows")
                    else:
                        print(f"  Loaded {key}: {value.get('type', 'unknown') if isinstance(value, dict) else 'unknown'}")
        
        if structures:
            all_structures.update(structures)
    
    print(f"\nTotal processed: {len(all_dataframes)} dataframes, {len(all_structures)} structures")
    
    # Integrate data within this directory
    print(f"\n=== Integrating Data Within Directory ===")
    
    # Group dataframes by type
    damon_dfs = {k: v for k, v in all_dataframes.items() if 'damon_data' in k}
    timestamped_dfs = {k: v for k, v in all_dataframes.items() 
                      if isinstance(v, pd.DataFrame) and 'timestamp_ns' in v.columns}
    
    print(f"Found {len(damon_dfs)} damon_data files")
    print(f"Found {len(timestamped_dfs)} timestamped dataframes")
    
    # Create integrated dataset for this directory
    integrated_df = None
    if timestamped_dfs:
        integrated_df = integrate_data(timestamped_dfs)
        
        if integrated_df is not None:
            print(f"Integrated dataset shape: {integrated_df.shape}")
            print("\nSample of integrated data:")
            print(integrated_df.head())
    
    return all_dataframes, all_structures, integrated_df

def process_directories(directories):
    """Process multiple directories and return integrated data for each directory"""
    all_dataframes = {}
    all_structures = {}
    integrated_dfs = {}  # Store integrated DataFrame for each directory
    
    for i, directory in enumerate(directories, 1):
        print(f"\n--- Directory {i}: {directory} ---")
        
        dataframes, structures, integrated_df = process_directory(directory)
        
        # Extract variant name from path like:
        # .../my_prcl_rss_409600_cold_500ms/01/parsed
        # We need to extract "my_prcl_rss_409600_cold_500ms"
        parsed_dir = directory.rstrip(os.sep)
        if parsed_dir.endswith('parsed'):
            # Remove /parsed
            parent_dir = os.path.dirname(parsed_dir)
            # Check if parent is '01' and navigate one more level up
            if os.path.basename(parent_dir) == '01':
                # Navigate up one more level to get the actual variant name
                variant_dir = os.path.dirname(parent_dir)
                variant_name = os.path.basename(variant_dir)
            else:
                variant_name = os.path.basename(parent_dir)
        else:
            # Fallback for other cases
            variant_name = os.path.basename(parsed_dir)
        
        if not variant_name or variant_name == 'parsed':  # Fallback if we can't extract variant
            variant_name = f"variant_{i}"
        
        # Store with variant prefix to avoid filename conflicts
        for key, value in dataframes.items():
            all_dataframes[f"{variant_name}_{key}"] = value
        
        # Store structures with variant prefix
        if structures:
            all_structures[variant_name] = structures
            
        # Store integrated DataFrame for this variant
        if integrated_df is not None:
            integrated_dfs[variant_name] = integrated_df
    
    return all_dataframes, all_structures, integrated_dfs

def main():
    parser = argparse.ArgumentParser(description='Analyze DAMON data from multiple directories')
    parser.add_argument('output_dir', help='Output directory path for analysis results')
    parser.add_argument('input_dirs', nargs='+', help='Input directory paths containing CSV files')
    
    args = parser.parse_args()
    
    # Validate output directory
    output_dir = Path(args.output_dir)
    print(f"Output directory: {output_dir.absolute()}")
    
    if not output_dir.exists():
        print(f"Output directory does not exist, creating: {output_dir.absolute()}")
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Validate input directories
    valid_directories = []
    for input_dir in args.input_dirs:
        dir_path = Path(input_dir)
        if dir_path.exists() and dir_path.is_dir():
            valid_directories.append(str(dir_path.absolute()))
        else:
            print(f"Warning: Invalid directory: {input_dir}")
    
    if not valid_directories:
        print("Error: No valid directories found")
        return
    
    print(f"Found {len(valid_directories)} valid directories")
    
    # Process all directories
    all_dataframes, all_structures, integrated_dfs = process_directories(valid_directories)
    
    # Extract RSS, VSZ and MAJFLT data from integrated dataframes
    print(f"\n=== Extracting RSS, VSZ, MAJFLT and PSI Data from Integrated Data ===")
    
    plot_data = []
    psi_plot_data = []
    
    for dir_name, integrated_df in integrated_dfs.items():
        if integrated_df is None or integrated_df.empty:
            continue
            
        print(f"\n--- Processing Integrated Data for {dir_name} ---")
        
        # Find relevant columns in the integrated dataframe
        rss_cols = [col for col in integrated_df.columns if 'rss' in col.lower() or 'res_set_size' in col.lower()]
        vsz_cols = [col for col in integrated_df.columns if 'vsz' in col.lower() or 'vm_size' in col.lower()]
        majflt_cols = [col for col in integrated_df.columns if 'majflt' in col.lower() or 'pgmajfaults' in col.lower()]
        psi_cols = [col for col in integrated_df.columns if 'psi' in col.lower() and 'some' in col.lower()]
        
        if not rss_cols or not vsz_cols:
            print(f"  Warning: Missing required columns. RSS: {rss_cols}, VSZ: {vsz_cols}")
            continue
        
        # Extract RSS and VSZ
        rss_col = rss_cols[0]
        vsz_col = vsz_cols[0]
        
        # Create a working copy
        df = integrated_df.copy()
        
        # Calculate RSS/VSZ ratio
        df['rss_vsz_ratio'] = df[rss_col] / df[vsz_col].replace(0, np.nan)
        
        # Process MAJFLT data
        if majflt_cols:
            majflt_col = majflt_cols[0]
            df_majflt = df.dropna(subset=['rss_vsz_ratio', majflt_col])
            
            if not df_majflt.empty:
                plot_data.append({
                    'source': dir_name,
                    'x_data': df_majflt['rss_vsz_ratio'],
                    'y_data': df_majflt[majflt_col],
                    'rss_col': rss_col,
                    'vsz_col': vsz_col,
                    'majflt_col': majflt_col,
                    'points': len(df_majflt)
                })
                print(f"  Extracted {len(df_majflt)} MAJFLT points")
        else:
            print("  Warning: No MAJFLT columns found")

        # Process PSI data
        if psi_cols:
            psi_col = psi_cols[0]
            df_psi = df.dropna(subset=['rss_vsz_ratio', psi_col])
            
            if not df_psi.empty:
                psi_plot_data.append({
                    'source': dir_name,
                    'x_data': df_psi['rss_vsz_ratio'],
                    'y_data': df_psi[psi_col],
                    'rss_col': rss_col,
                    'vsz_col': vsz_col,
                    'psi_col': psi_col,
                    'points': len(df_psi)
                })
                print(f"  Extracted {len(df_psi)} PSI points")
        else:
            print("  Warning: No PSI columns found")
    
    # Create plots for MAJFLT
    if plot_data:
        # 1. Original combined plot
        plot_output = output_dir / "majflt_rss_vsz_ratio_relationship.png"
        create_plot(plot_data, plot_output, "All Variants: MAJFLT Count vs RSS/VSZ Ratio", ylabel='MAJFLT Count')

        # Group data
        by_rss = {}
        by_threshold = {}
        
        for data in plot_data:
            variant = data['source']
            rss, threshold = parse_variant_params(variant)
            data['rss_param'] = rss
            data['threshold_param'] = threshold
            
            if rss not in by_rss: by_rss[rss] = []
            by_rss[rss].append(data)
            
            if threshold not in by_threshold: by_threshold[threshold] = []
            by_threshold[threshold].append(data)
            
        # 2. Group by RSS (Control Variable: RSS)
        print("\nGenerating MAJFLT plots grouped by RSS...")
        for rss, group_data in by_rss.items():
            output_path = output_dir / f"majflt_vs_ratio_rss_{rss}.png"
            title = f"MAJFLT vs RSS/VSZ (Fixed RSS: {rss})"
            create_plot(group_data, output_path, title, ylabel='MAJFLT Count')
            
        # 3. Group by Threshold (Control Variable: Threshold)
        print("\nGenerating MAJFLT plots grouped by Threshold...")
        for threshold, group_data in by_threshold.items():
            output_path = output_dir / f"majflt_vs_ratio_threshold_{threshold}.png"
            title = f"MAJFLT vs RSS/VSZ (Fixed Threshold: {threshold})"
            create_plot(group_data, output_path, title, ylabel='MAJFLT Count')

    else:
        print("No valid RSS/VSZ/MAJFLT data found in any integrated dataframe")

    # Create plots for PSI
    if psi_plot_data:
        # 1. Original combined plot
        plot_output = output_dir / "psi_rss_vsz_ratio_relationship.png"
        create_plot(psi_plot_data, plot_output, "All Variants: PSI Some vs RSS/VSZ Ratio", ylabel='PSI Some')

        # Group data
        by_rss_psi = {}
        by_threshold_psi = {}
        
        for data in psi_plot_data:
            variant = data['source']
            rss, threshold = parse_variant_params(variant)
            data['rss_param'] = rss
            data['threshold_param'] = threshold
            
            if rss not in by_rss_psi: by_rss_psi[rss] = []
            by_rss_psi[rss].append(data)
            
            if threshold not in by_threshold_psi: by_threshold_psi[threshold] = []
            by_threshold_psi[threshold].append(data)
            
        # 2. Group by RSS (Control Variable: RSS)
        print("\nGenerating PSI plots grouped by RSS...")
        for rss, group_data in by_rss_psi.items():
            output_path = output_dir / f"psi_vs_ratio_rss_{rss}.png"
            title = f"PSI Some vs RSS/VSZ (Fixed RSS: {rss})"
            create_plot(group_data, output_path, title, ylabel='PSI Some')
            
        # 3. Group by Threshold (Control Variable: Threshold)
        print("\nGenerating PSI plots grouped by Threshold...")
        for threshold, group_data in by_threshold_psi.items():
            output_path = output_dir / f"psi_vs_ratio_threshold_{threshold}.png"
            title = f"PSI Some vs RSS/VSZ (Fixed Threshold: {threshold})"
            create_plot(group_data, output_path, title, ylabel='PSI Some')

    else:
        print("No valid RSS/VSZ/PSI data found in any integrated dataframe")
    
    # Save metadata
    plot_summary = {
        'processed_directories': len(plot_data),
        'total_integrated_directories': len(integrated_dfs),
        'total_data_points': sum(data['points'] for data in plot_data),
        'directories_summary': [
            {
                'name': data['source'],
                'points': data['points'],
                'rss_column': data.get('rss_col'),
                'vsz_column': data.get('vsz_column'),
                'majflt_column': data.get('majflt_col')
            } for data in plot_data
        ]
    }
    
    metadata = {
        'input_directories': valid_directories,
        'file_structures': all_structures,
        'plot_summary': plot_summary,
        'data_summary': {
            'total_dataframes': len(all_dataframes),
            'processed_directories': len(valid_directories)
        }
    }
    
    metadata_file = output_dir / "analysis_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    
    print(f"\nAnalysis complete!")
    print(f"Plot saved to: {output_dir / 'majflt_rss_vsz_ratio_relationship.png'}")
    print(f"Metadata saved to: {metadata_file}")

if __name__ == "__main__":
    main()
