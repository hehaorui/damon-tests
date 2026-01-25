#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0

"""
Script to align and merge all timestamped CSV files to 100ms grid.

This script reads all CSV files containing nanosecond timestamps from a
parsed directory, aligns them to a 100ms time grid using nearest neighbor
interpolation, and saves the merged result back to the same directory.
"""

import sys
import os
import re
import glob
import pandas as pd
from typing import List, Dict, Optional


def find_ts_files(parsed_dir: str) -> List[str]:
    """
    Find all CSV files in parsed directory that contain timestamp column.

    Args:
        parsed_dir: Path to the parsed directory

    Returns:
        List of CSV file paths containing timestamp_ns column
    """
    # List all CSV files in the directory
    csv_files = glob.glob(os.path.join(parsed_dir, "*.csv"))

    # Filter files that have timestamp_ns column
    ts_files = []
    for f in csv_files:
        try:
            # Read first few lines to check for timestamp column
            with open(f, 'r') as file:
                first_line = file.readline().strip()
                if 'timestamp_ns' in first_line:
                    ts_files.append(f)
        except Exception as e:
            print(f"Warning: Could not read {f}: {e}", file=sys.stderr)

    return ts_files


def load_csvs(file_paths: List[str]) -> List[Dict[str, pd.DataFrame]]:
    """
    Load CSV files and extract timestamp and data columns.

    Args:
        file_paths: List of CSV file paths

    Returns:
        List of dictionaries containing filename and DataFrame data
        Each dict: {'name': str, 'df': pd.DataFrame}
    """
    loaded_data = []

    for f in file_paths:
        try:
            # Read CSV file
            df = pd.read_csv(f)

            # Check if timestamp_ns column exists
            if 'timestamp_ns' not in df.columns:
                print(f"Warning: {f} has no timestamp_ns column, skipping",
                      file=sys.stderr)
                continue

            # Extract filename without extension for column naming
            filename = os.path.basename(f).replace('.csv', '')

            loaded_data.append({
                'name': filename,
                'df': df
            })

        except Exception as e:
            print(f"Error loading {f}: {e}", file=sys.stderr)

    return loaded_data


def get_time_range(data_list: List[Dict[str, pd.DataFrame]]) -> tuple:
    """
    Get the global time range across all data files.

    Args:
        data_list: List of dictionaries containing DataFrame data

    Returns:
        Tuple of (start_time_ns, end_time_ns) in nanoseconds
    """
    # Initialize with None
    start_time: Optional[int] = None
    end_time: Optional[int] = None

    # Find min and max timestamps across all data
    for item in data_list:
        df = item['df']
        min_ts = df['timestamp_ns'].min()
        max_ts = df['timestamp_ns'].max()

        if start_time is None or min_ts < start_time:
            start_time = int(min_ts)

        if end_time is None or max_ts > end_time:
            end_time = int(max_ts)

    # Return as tuple
    return (start_time, end_time) if start_time is not None else (0, 0)


def create_time_grid(start_ns: int, end_ns: int, grid_ms: int = 100) -> pd.DatetimeIndex:
    """
    Create a time grid with specified interval.

    Args:
        start_ns: Start time in nanoseconds
        end_ns: End time in nanoseconds
        grid_ms: Grid interval in milliseconds (default: 100)

    Returns:
        DatetimeIndex representing the time grid
    """
    # Convert to milliseconds for pandas datetime
    start_ms = start_ns // 1_000_000
    end_ms = end_ns // 1_000_000

    # Create range in milliseconds
    grid_ms_range = pd.RangeIndex(start_ms, end_ms + grid_ms, grid_ms)

    # Convert to datetime index
    grid_time = pd.to_datetime(grid_ms_range, unit='ms')

    return grid_time


def align_to_grid(df: pd.DataFrame, grid_time: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Align DataFrame to time grid using nearest neighbor interpolation.

    Args:
        df: DataFrame with timestamp_ns column and other data columns
        grid_time: Time grid to align to

    Returns:
        DataFrame aligned to the grid with timestamp_dt as index
    """
    # Convert timestamp_ns to datetime (nanoseconds) for alignment
    df['timestamp_dt'] = pd.to_datetime(df['timestamp_ns'], unit='ns')

    # Set timestamp as index
    df = df.set_index('timestamp_dt')

    # Get data columns (exclude timestamp_ns which is now index)
    data_cols = df.columns.drop('timestamp_ns')

    # Reindex to grid using nearest neighbor interpolation
    df_aligned = df[data_cols].reindex(grid_time, method='nearest')

    return df_aligned


def merge_data(data_list: List[Dict[str, pd.DataFrame]],
               grid_time: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Merge all aligned DataFrames into single DataFrame.

    Args:
        data_list: List of dictionaries containing DataFrame data
        grid_time: Time grid used for alignment

    Returns:
        Merged DataFrame with time as index and columns for each metric
    """
    merged_df = pd.DataFrame(index=grid_time)

    for item in data_list:
        df = item['df']
        name = item['name']

        # Align this DataFrame to grid
        aligned = align_to_grid(df, grid_time)

        # Rename columns with filename prefix
        renamed = aligned.add_prefix(f'{name}_')

        # Merge into result
        merged_df = pd.concat([merged_df, renamed], axis=1)

    # Add millisecond timestamp column for reference
    merged_df['timestamp_ms'] = grid_time.astype('int64') // 1_000_000

    return merged_df


def save_csv(df: pd.DataFrame, output_path: str) -> None:
    """
    Save DataFrame to CSV file using temporary file for atomicity.

    Args:
        df: DataFrame to save
        output_path: Path for output CSV file
    """
    # Create temporary file path
    # temp_path: str - path to temporary CSV file
    temp_path = output_path + '.tmp'

    # Reset index to include timestamp as column
    df_output = df.reset_index(drop=True)

    # Save to temporary file first
    df_output.to_csv(temp_path, index=False)

    # Atomically rename to final destination
    os.rename(temp_path, output_path)

    print(f"Saved aligned data to {output_path}")


def process_parsed_dir(parsed_dir: str) -> int:
    """
    Process a single parsed directory to create aligned CSV.

    Args:
        parsed_dir: Path to the parsed directory

    Returns:
        0 on success, 1 on failure
    """
    # Find timestamped CSV files
    # ts_files: List[str] - paths to CSV files with timestamp_ns column
    ts_files = find_ts_files(parsed_dir)

    if not ts_files:
        print(f"No timestamped CSV files found in {parsed_dir}", file=sys.stderr)
        return 1

    print(f"Found {len(ts_files)} timestamped files in {parsed_dir}")

    # Load CSV files
    # loaded_data: List[Dict[str, pd.DataFrame]] - loaded data with metadata
    loaded_data = load_csvs(ts_files)

    if not loaded_data:
        print("No valid data loaded", file=sys.stderr)
        return 1

    # Get global time range
    # start_time_ns: int - earliest timestamp in nanoseconds
    # end_time_ns: int - latest timestamp in nanoseconds
    start_time_ns, end_time_ns = get_time_range(loaded_data)

    print(f"Time range: {start_time_ns} ns to {end_time_ns} ns")

    # Create 100ms time grid
    # grid_time: pd.DatetimeIndex - time points at 100ms intervals
    grid_time = create_time_grid(start_time_ns, end_time_ns, grid_ms=100)

    print(f"Created grid with {len(grid_time)} points")

    # Merge all data to grid
    # merged_df: pd.DataFrame - combined data aligned to time grid
    merged_df = merge_data(loaded_data, grid_time)

    # Save to parsed directory
    output_path = os.path.join(parsed_dir, 'integrated_data.csv')
    save_csv(merged_df, output_path)

    return 0


def main():
    """Main entry point for the script."""
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <parsed_directory>", file=sys.stderr)
        sys.exit(1)

    parsed_dir = sys.argv[1]

    if not os.path.isdir(parsed_dir):
        print(f"Error: {parsed_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    # Process the directory
    result = process_parsed_dir(parsed_dir)
    sys.exit(result)


if __name__ == "__main__":
    main()
