#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

"""
Script to plot relationships between metrics across workloads and variants.

This script automatically discovers all workload/variant combinations from
the results-collect directory, reads majflt_swaprate.csv and psi_swaprate.csv
from stat directories, and creates scatter and violin plots:
1. majflt_count vs swaprate_bp scatter plot
2. psi_mem_increment vs swaprate_bp scatter plot
3. majflt_count distribution violin plots
4. psi_mem_increment distribution violin plots

Different workloads/variants are distinguished by color and labels.
"""

import sys
import os
import glob
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple


def load_majflt_swaprate(stat_dir: str) -> Optional[pd.DataFrame]:
    """
    Load majflt_swaprate.csv file.

    Args:
        stat_dir: Path to stat directory

    Returns:
        DataFrame with run_id, majflt_count, and swaprate_bp columns,
        or None if file doesn't exist
    """
    csv_path = os.path.join(stat_dir, 'majflt_swaprate.csv')
    
    if not os.path.isfile(csv_path):
        print(f"Warning: {csv_path} not found, skipping", file=sys.stderr)
        return None
    
    try:
        df = pd.read_csv(csv_path)
        return df
    except Exception as e:
        print(f"Error loading {csv_path}: {e}", file=sys.stderr)
        return None


def load_psi_swaprate(stat_dir: str) -> Optional[pd.DataFrame]:
    """
    Load psi_swaprate.csv file.

    Args:
        stat_dir: Path to stat directory

    Returns:
        DataFrame with run_id, psi_mem_increment, and swaprate_bp columns,
        or None if file doesn't exist
    """
    csv_path = os.path.join(stat_dir, 'psi_swaprate.csv')
    
    if not os.path.isfile(csv_path):
        print(f"Warning: {csv_path} not found, skipping", file=sys.stderr)
        return None
    
    try:
        df = pd.read_csv(csv_path)
        return df
    except Exception as e:
        print(f"Error loading {csv_path}: {e}", file=sys.stderr)
        return None


def load_integrated_data(parsed_dir: str) -> Optional[pd.DataFrame]:
    """
    Load integrated_data.csv file from parsed directory.

    Args:
        parsed_dir: Path to parsed directory

    Returns:
        DataFrame with psi and majflt data, or None if file doesn't exist
    """
    csv_path = os.path.join(parsed_dir, 'integrated_data.csv')
    
    if not os.path.isfile(csv_path):
        print(f"Warning: {csv_path} not found, skipping", file=sys.stderr)
        return None
    
    try:
        df = pd.read_csv(csv_path)
        return df
    except Exception as e:
        print(f"Error loading {csv_path}: {e}", file=sys.stderr)
        return None


def find_workloads_and_variants(base_dir: str) -> List[Tuple[str, str, str]]:
    """
    Find all workload and variant combinations in results-collect directory.

    Args:
        base_dir: Base directory (results-collect)

    Returns:
        List of tuples (category, workload, variant)
    """
    combinations = []

    if not os.path.isdir(base_dir):
        return combinations

    for category in os.listdir(base_dir):
        category_path = os.path.join(base_dir, category)
        if not os.path.isdir(category_path):
            continue

        for workload in os.listdir(category_path):
            workload_path = os.path.join(category_path, workload)
            if not os.path.isdir(workload_path):
                continue

            for variant in os.listdir(workload_path):
                variant_path = os.path.join(workload_path, variant)
                if not os.path.isdir(variant_path):
                    continue

                stat_dir = os.path.join(variant_path, 'stat')
                if os.path.isdir(stat_dir):
                    combinations.append((category, workload, variant))

    return combinations


def load_all_variants(results_base: str) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Load data for all workload/variant combinations.

    Args:
        results_base: Base results directory path

    Returns:
        Dictionary mapping variant keys to dict with 'majflt', 'psi' DataFrames
        and metadata
    """
    all_data = {}

    combinations = find_workloads_and_variants(results_base)

    for category, workload, variant in combinations:
        variant_path = os.path.join(results_base, category, workload, variant)
        stat_dir = os.path.join(variant_path, 'stat')

        variant_data = {}
        variant_data['category'] = category
        variant_data['workload'] = workload
        variant_data['variant'] = variant

        # Load majflt_swaprate data
        majflt_df = load_majflt_swaprate(stat_dir)
        if majflt_df is not None and not majflt_df.empty:
            variant_data['majflt'] = majflt_df

        # Load psi_swaprate data
        psi_df = load_psi_swaprate(stat_dir)
        if psi_df is not None and not psi_df.empty:
            variant_data['psi'] = psi_df

        if 'majflt' in variant_data or 'psi' in variant_data:
            # Create a unique key: category/workload/variant
            variant_key = f"{category}/{workload}/{variant}"
            all_data[variant_key] = variant_data

    return all_data


def create_variant_name(variant_key: str) -> str:
    """
    Create a readable name for variant including workload info.

    Args:
        variant_key: Full variant path (e.g., splash2x/radix/my_prcl_swaprate_10_cold_1500ms)

    Returns:
        Readable name with workload and variant info
    """
    parts = variant_key.split('/')
    if len(parts) >= 3:
        # Return "workload/variant" for clarity
        return f"{parts[1]}/{parts[2]}"
    elif len(parts) == 2:
        return f"{parts[0]}/{parts[1]}"
    return variant_key if parts else variant_key


def create_short_label(variant_key: str) -> str:
    """
    Create a short label for plotting (workload only).

    Args:
        variant_key: Full variant path

    Returns:
        Short workload name
    """
    parts = variant_key.split('/')
    if len(parts) >= 2:
        return parts[1]  # Return workload name
    return variant_key if parts else variant_key


def plot_majflt_swaprate(all_data: Dict[str, Dict[str, pd.DataFrame]],
                         output_path: str) -> None:
    """
    Create scatter plot of majflt_count vs swaprate_bp.

    Args:
        all_data: Dictionary of variant data
        output_path: Path to save the plot
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    colors = plt.cm.tab20(np.linspace(0, 1, min(20, len(all_data))))
    
    for i, (variant, data) in enumerate(sorted(all_data.items())):
        if 'majflt' not in data:
            continue
        
        df = data['majflt']
        color = colors[i % len(colors)]
        
        # Plot scatter points
        ax.scatter(df['swaprate_bp'], df['majflt_count'],
                  alpha=0.6, label=create_variant_name(variant),
                  color=color, s=50)
    
    ax.set_xlabel('Swap Rate (basis points)', fontsize=12)
    ax.set_ylabel('Major Fault Count', fontsize=12)
    ax.set_title('Major Fault Count vs Swap Rate', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_yscale('log')
    
    # Add legend
    if len(all_data) <= 15:
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    else:
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7,
                  ncol=2)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved majflt_swaprate plot to {output_path}")
    plt.close()


def plot_psi_swaprate(all_data: Dict[str, Dict[str, pd.DataFrame]],
                      output_path: str) -> None:
    """
    Create scatter plot of psi_mem_increment vs swaprate_bp.

    Args:
        all_data: Dictionary of variant data
        output_path: Path to save the plot
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    colors = plt.cm.tab20(np.linspace(0, 1, min(20, len(all_data))))
    
    for i, (variant, data) in enumerate(sorted(all_data.items())):
        if 'psi' not in data:
            continue
        
        df = data['psi']
        color = colors[i % len(colors)]
        
        # Plot scatter points
        ax.scatter(df['swaprate_bp'], df['psi_mem_increment'],
                  alpha=0.6, label=create_variant_name(variant),
                  color=color, s=50)
    
    ax.set_xlabel('Swap Rate (basis points)', fontsize=12)
    ax.set_ylabel('PSI Memory Some Increment', fontsize=12)
    ax.set_title('PSI Memory Increment vs Swap Rate', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_yscale('log')
    
    # Add legend
    if len(all_data) <= 15:
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    else:
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7,
                  ncol=2)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved psi_swaprate plot to {output_path}")
    plt.close()


def plot_majflt_distribution(all_data: Dict[str, Dict[str, pd.DataFrame]],
                            output_path: str) -> None:
    """
    Create violin plot of majflt_count distribution across variants.

    Args:
        all_data: Dictionary of variant data
        output_path: Path to save the plot
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Collect data for each variant
    variant_names = []
    majflt_data = []
    
    for variant in sorted(all_data.keys()):
        if 'majflt' not in all_data[variant]:
            continue
        
        df = all_data[variant]['majflt']
        # Filter out NaN values
        majflt_values = df['majflt_count'].dropna().values
        if len(majflt_values) > 0:
            variant_names.append(create_variant_name(variant))
            majflt_data.append(majflt_values)
    
    # Create violin plot
    parts = ax.violinplot(majflt_data, positions=range(len(variant_names)),
                           showmeans=True, showmedians=True, showextrema=True)
    
    # Color the violin plots
    colors = plt.cm.tab20(np.linspace(0, 1, min(20, len(majflt_data))))
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(colors[i])
        pc.set_alpha(0.7)
    
    ax.set_xticks(range(len(variant_names)))
    ax.set_xticklabels(variant_names)
    ax.set_ylabel('Major Fault Count', fontsize=12)
    ax.set_title('Major Fault Count Distribution', fontsize=14, fontweight='bold')
    
    # Use log scale if all values are positive
    if majflt_data and all(np.all(data > 0) for data in majflt_data):
        ax.set_yscale('log')
    else:
        print("Warning: Some majflt_count values are non-positive, using linear scale",
              file=sys.stderr)
    
    ax.grid(True, alpha=0.3, axis='y')
    
    # Rotate x-axis labels if many variants
    if len(variant_names) > 5:
        plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved majflt distribution plot to {output_path}")
    plt.close()


def plot_psi_distribution(all_data: Dict[str, Dict[str, pd.DataFrame]],
                         output_path: str) -> None:
    """
    Create violin plot of psi_mem_increment distribution across variants.

    Args:
        all_data: Dictionary of variant data
        output_path: Path to save the plot
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Collect data for each variant
    variant_names = []
    psi_data = []
    
    for variant in sorted(all_data.keys()):
        if 'psi' not in all_data[variant]:
            continue
        
        df = all_data[variant]['psi']
        # Filter out NaN values
        psi_values = df['psi_mem_increment'].dropna().values
        if len(psi_values) > 0:
            variant_names.append(create_variant_name(variant))
            psi_data.append(psi_values)
    
    # Create violin plot
    parts = ax.violinplot(psi_data, positions=range(len(variant_names)),
                           showmeans=True, showmedians=True, showextrema=True)
    
    # Color the violin plots
    colors = plt.cm.tab20(np.linspace(0, 1, min(20, len(psi_data))))
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(colors[i])
        pc.set_alpha(0.7)
    
    ax.set_xticks(range(len(variant_names)))
    ax.set_xticklabels(variant_names)
    ax.set_ylabel('PSI Memory Some Increment', fontsize=12)
    ax.set_title('PSI Memory Increment Distribution', fontsize=14, fontweight='bold')
    
    # Use log scale if all values are positive
    if psi_data and all(np.all(data > 0) for data in psi_data):
        ax.set_yscale('log')
    else:
        print("Warning: Some psi_mem_increment values are non-positive, using linear scale",
              file=sys.stderr)
    
    ax.grid(True, alpha=0.3, axis='y')
    
    # Rotate x-axis labels if many variants
    if len(variant_names) > 5:
        plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved psi distribution plot to {output_path}")
    plt.close()


def plot_majflt_distribution_log(all_data: Dict[str, Dict[str, pd.DataFrame]],
                                output_path: str) -> None:
    """
    Create violin plot of majflt_count distribution across variants with log scale.

    Args:
        all_data: Dictionary of variant data
        output_path: Path to save the plot
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Collect data for each variant (only positive values)
    variant_names = []
    majflt_data = []
    
    for variant in sorted(all_data.keys()):
        if 'majflt' not in all_data[variant]:
            continue
        
        df = all_data[variant]['majflt']
        # Filter out NaN and non-positive values for log scale
        majflt_values = df['majflt_count'].dropna()
        majflt_values = majflt_values[majflt_values > 0].values
        if len(majflt_values) > 0:
            variant_names.append(create_variant_name(variant))
            majflt_data.append(majflt_values)
    
    if not majflt_data:
        print("Warning: No positive majflt_count values found for log scale plot",
              file=sys.stderr)
        plt.close()
        return
    
    # Create violin plot
    parts = ax.violinplot(majflt_data, positions=range(len(variant_names)),
                           showmeans=True, showmedians=True, showextrema=True)
    
    # Color is violin plots
    colors = plt.cm.tab20(np.linspace(0, 1, min(20, len(majflt_data))))
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(colors[i])
        pc.set_alpha(0.7)
    
    ax.set_xticks(range(len(variant_names)))
    ax.set_xticklabels(variant_names)
    ax.set_ylabel('Major Fault Count', fontsize=12)
    ax.set_title('Major Fault Count Distribution (Log Scale)', fontsize=14, fontweight='bold')
    ax.set_yscale('log')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Rotate x-axis labels if many variants
    if len(variant_names) > 5:
        plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved majflt distribution plot (log scale) to {output_path}")
    plt.close()


def plot_psi_distribution_log(all_data: Dict[str, Dict[str, pd.DataFrame]],
                              output_path: str) -> None:
    """
    Create violin plot of psi_mem_increment distribution across variants with log scale.

    Args:
        all_data: Dictionary of variant data
        output_path: Path to save the plot
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Collect data for each variant (only positive values)
    variant_names = []
    psi_data = []
    
    for variant in sorted(all_data.keys()):
        if 'psi' not in all_data[variant]:
            continue
        
        df = all_data[variant]['psi']
        # Filter out NaN and non-positive values for log scale
        psi_values = df['psi_mem_increment'].dropna()
        psi_values = psi_values[psi_values > 0].values
        if len(psi_values) > 0:
            variant_names.append(create_variant_name(variant))
            psi_data.append(psi_values)
    
    if not psi_data:
        print("Warning: No positive psi_mem_increment values found for log scale plot",
              file=sys.stderr)
        plt.close()
        return
    
    # Create violin plot
    parts = ax.violinplot(psi_data, positions=range(len(variant_names)),
                           showmeans=True, showmedians=True, showextrema=True)
    
    # Color the violin plots
    colors = plt.cm.tab20(np.linspace(0, 1, min(20, len(psi_data))))
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(colors[i])
        pc.set_alpha(0.7)
    
    ax.set_xticks(range(len(variant_names)))
    ax.set_xticklabels(variant_names)
    ax.set_ylabel('PSI Memory Some Increment', fontsize=12)
    ax.set_title('PSI Memory Increment Distribution (Log Scale)', fontsize=14, fontweight='bold')
    ax.set_yscale('log')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Rotate x-axis labels if many variants
    if len(variant_names) > 5:
        plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved psi distribution plot (log scale) to {output_path}")
    plt.close()


def plot_majflt_distribution_filtered(all_data: Dict[str, Dict[str, pd.DataFrame]],
                                     output_path: str) -> None:
    """
    Create violin plot of majflt_count distribution across variants with linear scale,
    excluding zero values.

    Args:
        all_data: Dictionary of variant data
        output_path: Path to save plot
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Collect data for each variant (only positive values)
    variant_names = []
    majflt_data = []
    
    for variant in sorted(all_data.keys()):
        if 'majflt' not in all_data[variant]:
            continue
        
        df = all_data[variant]['majflt']
        # Filter out NaN and zero values
        majflt_values = df['majflt_count'].dropna()
        majflt_values = majflt_values[majflt_values > 0].values
        if len(majflt_values) > 0:
            variant_names.append(create_variant_name(variant))
            majflt_data.append(majflt_values)
    
    if not majflt_data:
        print("Warning: No non-zero majflt_count values found for filtered plot",
              file=sys.stderr)
        plt.close()
        return
    
    # Create violin plot
    parts = ax.violinplot(majflt_data, positions=range(len(variant_names)),
                           showmeans=True, showmedians=True, showextrema=True)
    
    # Color is violin plots
    colors = plt.cm.tab20(np.linspace(0, 1, min(20, len(majflt_data))))
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(colors[i])
        pc.set_alpha(0.7)
    
    ax.set_xticks(range(len(variant_names)))
    ax.set_xticklabels(variant_names)
    ax.set_ylabel('Major Fault Count', fontsize=12)
    ax.set_title('Major Fault Count Distribution (Non-Zero)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Rotate x-axis labels if many variants
    if len(variant_names) > 5:
        plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved majflt distribution plot (non-zero) to {output_path}")
    plt.close()


def plot_psi_distribution_filtered(all_data: Dict[str, Dict[str, pd.DataFrame]],
                                    output_path: str) -> None:
    """
    Create violin plot of psi_mem_increment distribution across variants with linear scale,
    excluding zero values.

    Args:
        all_data: Dictionary of variant data
        output_path: Path to save the plot
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Collect data for each variant (only positive values)
    variant_names = []
    psi_data = []
    
    for variant in sorted(all_data.keys()):
        if 'psi' not in all_data[variant]:
            continue
        
        df = all_data[variant]['psi']
        # Filter out NaN and zero values
        psi_values = df['psi_mem_increment'].dropna()
        psi_values = psi_values[psi_values > 0].values
        if len(psi_values) > 0:
            variant_names.append(create_variant_name(variant))
            psi_data.append(psi_values)
    
    if not psi_data:
        print("Warning: No non-zero psi_mem_increment values found for filtered plot",
              file=sys.stderr)
        plt.close()
        return
    
    # Create violin plot
    parts = ax.violinplot(psi_data, positions=range(len(variant_names)),
                           showmeans=True, showmedians=True, showextrema=True)
    
    # Color the violin plots
    colors = plt.cm.tab20(np.linspace(0, 1, min(20, len(psi_data))))
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(colors[i])
        pc.set_alpha(0.7)
    
    ax.set_xticks(range(len(variant_names)))
    ax.set_xticklabels(variant_names)
    ax.set_ylabel('PSI Memory Some Increment', fontsize=12)
    ax.set_title('PSI Memory Increment Distribution (Non-Zero)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Rotate x-axis labels if many variants
    if len(variant_names) > 5:
        plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved psi distribution plot (non-zero) to {output_path}")
    plt.close()


def plot_swaprate_distribution(all_data: Dict[str, Dict[str, pd.DataFrame]],
                             output_path: str) -> None:
    """
    Create violin plot of swaprate_bp distribution across variants.

    Args:
        all_data: Dictionary of variant data
        output_path: Path to save the plot
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    # Collect data for each variant
    variant_names = []
    swaprate_data = []

    for variant in sorted(all_data.keys()):
        # Try to get swaprate data from majflt dataframe
        if 'majflt' in all_data[variant]:
            df = all_data[variant]['majflt']
            swaprate_values = df['swaprate_bp'].dropna().values
        elif 'psi' in all_data[variant]:
            df = all_data[variant]['psi']
            swaprate_values = df['swaprate_bp'].dropna().values
        else:
            continue

        if len(swaprate_values) > 0:
            variant_names.append(create_variant_name(variant))
            swaprate_data.append(swaprate_values)

    # Create violin plot
    parts = ax.violinplot(swaprate_data, positions=range(len(variant_names)),
                           showmeans=True, showmedians=True, showextrema=True)

    # Color the violin plots
    colors = plt.cm.tab20(np.linspace(0, 1, min(20, len(swaprate_data))))
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(colors[i])
        pc.set_alpha(0.7)

    ax.set_xticks(range(len(variant_names)))
    ax.set_xticklabels(variant_names)
    ax.set_ylabel('Swap Rate (basis points)', fontsize=12)
    ax.set_title('Swap Rate Distribution', fontsize=14, fontweight='bold')

    # Use log scale if all values are positive
    if swaprate_data and all(np.all(data > 0) for data in swaprate_data):
        ax.set_yscale('log')
    else:
        print("Warning: Some swaprate_bp values are non-positive, using linear scale",
              file=sys.stderr)

    ax.grid(True, alpha=0.3, axis='y')

    # Rotate x-axis labels if many variants
    if len(variant_names) > 5:
        plt.xticks(rotation=45, ha='right')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved swaprate distribution plot to {output_path}")
    plt.close()


def plot_swaprate_distribution_log(all_data: Dict[str, Dict[str, pd.DataFrame]],
                                 output_path: str) -> None:
    """
    Create violin plot of swaprate_bp distribution across variants with log scale.

    Args:
        all_data: Dictionary of variant data
        output_path: Path to save the plot
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    # Collect data for each variant (only positive values)
    variant_names = []
    swaprate_data = []

    for variant in sorted(all_data.keys()):
        # Try to get swaprate data from majflt dataframe
        if 'majflt' in all_data[variant]:
            df = all_data[variant]['majflt']
            swaprate_values = df['swaprate_bp'].dropna()
            swaprate_values = swaprate_values[swaprate_values > 0].values
        elif 'psi' in all_data[variant]:
            df = all_data[variant]['psi']
            swaprate_values = df['swaprate_bp'].dropna()
            swaprate_values = swaprate_values[swaprate_values > 0].values
        else:
            continue

        if len(swaprate_values) > 0:
            variant_names.append(create_variant_name(variant))
            swaprate_data.append(swaprate_values)

    if not swaprate_data:
        print("Warning: No positive swaprate_bp values found for log scale plot",
              file=sys.stderr)
        plt.close()
        return

    # Create violin plot
    parts = ax.violinplot(swaprate_data, positions=range(len(variant_names)),
                           showmeans=True, showmedians=True, showextrema=True)

    # Color the violin plots
    colors = plt.cm.tab20(np.linspace(0, 1, min(20, len(swaprate_data))))
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(colors[i])
        pc.set_alpha(0.7)

    ax.set_xticks(range(len(variant_names)))
    ax.set_xticklabels(variant_names)
    ax.set_ylabel('Swap Rate (basis points)', fontsize=12)
    ax.set_title('Swap Rate Distribution (Log Scale)', fontsize=14, fontweight='bold')
    ax.set_yscale('log')
    ax.grid(True, alpha=0.3, axis='y')

    # Rotate x-axis labels if many variants
    if len(variant_names) > 5:
        plt.xticks(rotation=45, ha='right')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved swaprate distribution plot (log scale) to {output_path}")
    plt.close()


def plot_swaprate_distribution_filtered(all_data: Dict[str, Dict[str, pd.DataFrame]],
                                     output_path: str) -> None:
    """
    Create violin plot of swaprate_bp distribution across variants with linear scale,
    excluding zero values.

    Args:
        all_data: Dictionary of variant data
        output_path: Path to save the plot
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    # Collect data for each variant (only positive values)
    variant_names = []
    swaprate_data = []

    for variant in sorted(all_data.keys()):
        # Try to get swaprate data from majflt dataframe
        if 'majflt' in all_data[variant]:
            df = all_data[variant]['majflt']
            swaprate_values = df['swaprate_bp'].dropna()
            swaprate_values = swaprate_values[swaprate_values > 0].values
        elif 'psi' in all_data[variant]:
            df = all_data[variant]['psi']
            swaprate_values = df['swaprate_bp'].dropna()
            swaprate_values = swaprate_values[swaprate_values > 0].values
        else:
            continue

        if len(swaprate_values) > 0:
            variant_names.append(create_variant_name(variant))
            swaprate_data.append(swaprate_values)

    if not swaprate_data:
        print("Warning: No non-zero swaprate_bp values found for filtered plot",
              file=sys.stderr)
        plt.close()
        return

    # Create violin plot
    parts = ax.violinplot(swaprate_data, positions=range(len(variant_names)),
                           showmeans=True, showmedians=True, showextrema=True)

    # Color the violin plots
    colors = plt.cm.tab20(np.linspace(0, 1, min(20, len(swaprate_data))))
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(colors[i])
        pc.set_alpha(0.7)

    ax.set_xticks(range(len(variant_names)))
    ax.set_xticklabels(variant_names)
    ax.set_ylabel('Swap Rate (basis points)', fontsize=12)
    ax.set_title('Swap Rate Distribution (Non-Zero)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    # Rotate x-axis labels if many variants
    if len(variant_names) > 5:
        plt.xticks(rotation=45, ha='right')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved swaprate distribution plot (non-zero) to {output_path}")
    plt.close()


def plot_psi_majflt(all_data: Dict[str, Dict[str, pd.DataFrame]],
                   results_base: str,
                   output_path: str) -> None:
    """
    Create scatter plot of psi_mem_increment vs majflt_count from parsed/integrated_data.csv.

    Args:
        all_data: Dictionary of variant data (for category/workload/variant info)
        results_base: Base results directory path
        output_path: Path to save the plot
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    colors = plt.cm.tab20(np.linspace(0, 1, min(20, len(all_data))))
    
    for i, (variant, data) in enumerate(sorted(all_data.items())):
        category = data.get('category', '')
        workload = data.get('workload', '')
        variant_name = data.get('variant', '')
        
        if not category or not workload or not variant_name:
            continue
        
        variant_path = os.path.join(results_base, category, workload, variant_name)
        
        # Find the first run directory (01, 02, ...)
        run_dirs = sorted([d for d in os.listdir(variant_path) 
                          if os.path.isdir(os.path.join(variant_path, d)) and d.isdigit()])
        
        for run_dir in run_dirs:
            parsed_dir = os.path.join(variant_path, run_dir, 'parsed')
            df = load_integrated_data(parsed_dir)
            
            if df is None or df.empty:
                continue
            
            # Check if required columns exist
            if 'psi_mem_timestamped_some_increment' not in df.columns:
                continue
            if 'process_fault_count_timestamped.diff_majflt_count' not in df.columns:
                continue
            
            # Extract PSI and majflt columns
            psi_values = df['psi_mem_timestamped_some_increment'].values
            majflt_values = df['process_fault_count_timestamped.diff_majflt_count'].values
            
            # Filter out NaN values
            valid_mask = ~np.isnan(psi_values) & ~np.isnan(majflt_values)
            psi_values = psi_values[valid_mask]
            majflt_values = majflt_values[valid_mask]
            
            if len(psi_values) == 0:
                continue
            
            color = colors[i % len(colors)]
            
            # Plot scatter points
            ax.scatter(majflt_values, psi_values,
                      alpha=0.6, label=create_variant_name(variant),
                      color=color, s=30)
            break  # Only plot first run for each variant
    
    ax.set_xlabel('Major Fault Count', fontsize=12)
    ax.set_ylabel('PSI Memory Some Increment', fontsize=12)
    ax.set_title('PSI Memory Increment vs Major Fault Count', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')
    ax.set_yscale('log')
    
    # Add legend
    if len(all_data) <= 15:
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    else:
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7,
                  ncol=2)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved psi_majflt plot to {output_path}")
    plt.close()


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <results-collect-directory>",
              file=sys.stderr)
        sys.exit(1)

    results_base = sys.argv[1]

    # Load data for all workload/variant combinations automatically
    all_data = load_all_variants(results_base)

    if not all_data:
        print("No data found for any workload/variant", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded data for {len(all_data)} workload/variant combination(s)")

    # Create output directory if it doesn't exist
    analyze_dir = os.path.dirname(os.path.abspath(__file__))

    # Create scatter plots
    plot_majflt_swaprate(all_data,
                        os.path.join(analyze_dir, 'majflt_swaprate.png'))

    plot_psi_swaprate(all_data,
                      os.path.join(analyze_dir, 'psi_swaprate.png'))

    # Create distribution plots
    plot_majflt_distribution(all_data,
                            os.path.join(analyze_dir, 'majflt_distribution.png'))

    plot_psi_distribution(all_data,
                         os.path.join(analyze_dir, 'psi_distribution.png'))

    # Create distribution plots with log scale
    plot_majflt_distribution_log(all_data,
                                os.path.join(analyze_dir, 'majflt_distribution_log.png'))

    plot_psi_distribution_log(all_data,
                              os.path.join(analyze_dir, 'psi_distribution_log.png'))

    # Create distribution plots with filtered zero values
    plot_majflt_distribution_filtered(all_data,
                                     os.path.join(analyze_dir, 'majflt_distribution_nonzero.png'))

    plot_psi_distribution_filtered(all_data,
                                    os.path.join(analyze_dir, 'psi_distribution_nonzero.png'))

    # Create swaprate distribution plots
    plot_swaprate_distribution(all_data,
                             os.path.join(analyze_dir, 'swaprate_distribution.png'))

    plot_swaprate_distribution_log(all_data,
                                 os.path.join(analyze_dir, 'swaprate_distribution_log.png'))

    plot_swaprate_distribution_filtered(all_data,
                                     os.path.join(analyze_dir, 'swaprate_distribution_nonzero.png'))

    # Create PSI vs majflt scatter plot from parsed/integrated_data.csv
    plot_psi_majflt(all_data, results_base,
                   os.path.join(analyze_dir, 'psi_majflt.png'))


if __name__ == "__main__":
    main()
