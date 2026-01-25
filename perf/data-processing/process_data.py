#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

"""
Script to automatically collect data from all workloads/variants in results-collect.

This script scans the results-collect directory for all workload and variant
combinations, extracts two data pairs from integrated_data.csv files:
1. (majflt_count, swaprate_bp)
2. (psi_increment, swaprate_bp)
And saves merged data to per-variant stat directories.

Usage:
    _collect_results_collect.py <results-collect-directory>
"""

import sys
import os
import glob
import time
import pandas as pd
from typing import List, Optional, Tuple


def wait_for_file(file_path: str, max_wait: int = 60, check_interval: int = 1) -> bool:
    """
    Wait for a file to exist, with a timeout.

    Args:
        file_path: Path to file to wait for
        max_wait: Maximum time to wait in seconds (default: 60)
        check_interval: Time between checks in seconds (default: 1)

    Returns:
        True if file exists, False if timeout reached
    """
    elapsed = 0

    while elapsed < max_wait:
        if os.path.isfile(file_path):
            return True

        time.sleep(check_interval)
        elapsed += check_interval

    return False


def find_integrated_files(src_dirs: List[str], wait_timeout: int = 60) -> List[str]:
    """
    Find all integrated_data.csv files in source directories.

    Args:
        src_dirs: List of source directory paths (parsed directories)
        wait_timeout: Maximum time to wait for each file in seconds (default: 60)

    Returns:
        List of paths to integrated_data.csv files
    """
    csv_files = []

    for d in src_dirs:
        csv_path = os.path.join(d, 'integrated_data.csv')

        if not os.path.isfile(csv_path):
            if not wait_for_file(csv_path, max_wait=wait_timeout):
                print(f"Warning: {csv_path} not available after timeout, skipping",
                      file=sys.stderr)
                continue

        csv_files.append(csv_path)

    return csv_files


def load_and_extract_columns(file_path: str,
                              col1: str,
                              col2: str) -> Optional[pd.DataFrame]:
    """
    Load CSV file and extract two columns.

    Args:
        file_path: Path to integrated_data.csv file
        col1: Name of first column
        col2: Name of second column

    Returns:
        DataFrame with the two columns, or None if file cannot be loaded
    """
    try:
        df = pd.read_csv(file_path)

        if col1 not in df.columns or col2 not in df.columns:
            print(f"Warning: {file_path} missing required columns, skipping",
                  file=sys.stderr)
            return None

        df_extracted = df[[col1, col2]].copy()

        return df_extracted

    except Exception as e:
        print(f"Error loading {file_path}: {e}", file=sys.stderr)
        return None


def merge_runs(data_list: List[pd.DataFrame],
               src_dirs: List[str],
               col1: str,
               col2: str,
               output_col1: str,
               output_col2: str) -> pd.DataFrame:
    """
    Merge data from multiple runs into single DataFrame.

    Args:
        data_list: List of DataFrames from each run
        src_dirs: List of source directory paths for run ID extraction
        col1: Name of first column (input)
        col2: Name of second column (input)
        output_col1: Name for first column (output)
        output_col2: Name for second column (output)

    Returns:
        Merged DataFrame with run_id and the two output columns
    """
    merged_dfs = []

    for i, (df, src_dir) in enumerate(zip(data_list, src_dirs)):
        if df is None or df.empty:
            continue

        # Extract run ID from the parent directory name
        parent_dir = os.path.dirname(src_dir.rstrip('/'))
        run_id = os.path.basename(parent_dir)

        # Add run_id column
        df_copy = df.copy()
        df_copy['run_id'] = run_id

        # Rename columns to simpler names
        df_copy = df_copy.rename(columns={
            col1: output_col1,
            col2: output_col2
        })

        merged_dfs.append(df_copy)

    if not merged_dfs:
        return pd.DataFrame()

    result = pd.concat(merged_dfs, ignore_index=True)
    return result


def save_csv(df: pd.DataFrame, output_path: str) -> None:
    """
    Save DataFrame to CSV file using temporary file for atomicity.

    Args:
        df: DataFrame to save
        output_path: Path for output CSV file
    """
    temp_path = output_path + '.tmp'
    df.to_csv(temp_path, index=False)
    os.rename(temp_path, output_path)
    print(f"Saved merged data to {output_path}")


def process_variant(output_dir: str,
                    src_dirs: List[str],
                    wait_timeout: int = 60) -> Tuple[int, int]:
    """
    Process all run directories for a variant and create merged CSV files.

    Args:
        output_dir: Path to the output (stat) directory
        src_dirs: List of source (parsed) directory paths
        wait_timeout: Maximum time to wait for each file in seconds (default: 60)

    Returns:
        Tuple of (success_count, failure_count)
    """
    success_count = 0
    failure_count = 0

    # Find all integrated_data.csv files
    csv_files = find_integrated_files(src_dirs, wait_timeout=wait_timeout)

    if not csv_files:
        print(f"No integrated_data.csv files found in {src_dirs}", file=sys.stderr)
        return (0, 1)

    print(f"Found {len(csv_files)} integrated_data.csv files")

    # Process majflt_count and swaprate_bp
    majflt_col = 'process_fault_count_timestamped.diff_majflt_count'
    swaprate_col = 'swaprate_tuning_timestamped_swaprate_bp'

    data_list_majflt = []
    run_dirs = []
    for f in csv_files:
        df = load_and_extract_columns(f, majflt_col, swaprate_col)
        data_list_majflt.append(df)
        run_dirs.append(os.path.dirname(f))

    merged_df_majflt = merge_runs(data_list_majflt, run_dirs, majflt_col, swaprate_col,
                                   'majflt_count', 'swaprate_bp')

    if not merged_df_majflt.empty:
        output_path = os.path.join(output_dir, 'majflt_swaprate.csv')
        save_csv(merged_df_majflt, output_path)
        success_count += 1
    else:
        print(f"No majflt/swaprate data to save", file=sys.stderr)
        failure_count += 1

    # Process psi_increment and swaprate_bp
    psi_col = 'psi_mem_timestamped_some_increment'

    data_list_psi = []
    run_dirs = []
    for f in csv_files:
        df = load_and_extract_columns(f, psi_col, swaprate_col)
        data_list_psi.append(df)
        run_dirs.append(os.path.dirname(f))

    merged_df_psi = merge_runs(data_list_psi, run_dirs, psi_col, swaprate_col,
                               'psi_mem_increment', 'swaprate_bp')

    if not merged_df_psi.empty:
        output_path = os.path.join(output_dir, 'psi_swaprate.csv')
        save_csv(merged_df_psi, output_path)
        success_count += 1
    else:
        print(f"No PSI/swaprate data to save", file=sys.stderr)
        failure_count += 1

    return (success_count, failure_count)


def find_workloads_and_variants(base_dir: str) -> List[Tuple[str, str]]:
    """
    Find all workload and variant combinations in results-collect directory.

    Args:
        base_dir: Base directory (results-collect)

    Returns:
        List of tuples (workload_path, variant) where workload_path is the path
        relative to base_dir (e.g., "splash2x/radix")
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

            # Check if this contains run directories (variants)
            # Variants are directories that contain numeric run directories
            for variant in os.listdir(workload_path):
                variant_path = os.path.join(workload_path, variant)
                if not os.path.isdir(variant_path):
                    continue

                # Check if this variant contains numeric run directories
                has_run_dirs = any(
                    os.path.isdir(os.path.join(variant_path, r)) and
                    os.path.isdir(os.path.join(variant_path, r, 'parsed'))
                    for r in os.listdir(variant_path)
                )

                if has_run_dirs:
                    workload_rel = os.path.relpath(workload_path, base_dir)
                    combinations.append((workload_rel, variant))

    return combinations


def find_run_directories(variant_path: str) -> List[str]:
    """
    Find all run directories for a variant.

    Args:
        variant_path: Path to variant directory

    Returns:
        List of parsed directory paths
    """
    run_dirs = []

    for run in os.listdir(variant_path):
        run_path = os.path.join(variant_path, run)
        if not os.path.isdir(run_path):
            continue

        parsed_path = os.path.join(run_path, 'parsed')
        if os.path.isdir(parsed_path):
            run_dirs.append(parsed_path)

    return run_dirs


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <results-collect-directory>", file=sys.stderr)
        sys.exit(1)

    base_dir = sys.argv[1]

    # Find all workload and variant combinations
    combinations = find_workloads_and_variants(base_dir)

    if not combinations:
        print(f"No workload/variant combinations found in {base_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(combinations)} workload/variant combinations")

    total_success = 0
    total_failure = 0

    # Process each combination
    for workload_path, variant in combinations:
        print(f"Processing {workload_path}/{variant}...")

        variant_path = os.path.join(base_dir, workload_path, variant)
        run_dirs = find_run_directories(variant_path)

        if not run_dirs:
            print(f"Warning: No run directories found for {workload_path}/{variant}",
                  file=sys.stderr)
            total_failure += 2  # Count as two failures (majflt and psi)
            continue

        print(f"  Found {len(run_dirs)} run directories")

        # Create stat directory
        stat_dir = os.path.join(base_dir, workload_path, variant, 'stat')
        os.makedirs(stat_dir, exist_ok=True)

        # Process the variant
        success_count, failure_count = process_variant(stat_dir, run_dirs)
        total_success += success_count
        total_failure += failure_count

    print(f"\nSummary: {total_success} files saved successfully, {total_failure} failures")

    sys.exit(0 if total_failure == 0 else 1)


if __name__ == "__main__":
    main()
