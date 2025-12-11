#!/usr/bin/env python3

import sys
import os
import re

def parse_timestamped_file(input_file, output_file):
    """
    Parse timestamped pswpout data file and convert to CSV format with incremental values.
    
    Args:
        input_file: Path to the input timestamped file
        output_file: Path to the output CSV file
    """
    data = []
    previous_value = None
    
    try:
        with open(input_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Parse line format: [timestamp_ns] MetricName: value unit
                match = re.match(r'\[(\d+)\]\s+(\w+):\s+(\d+)\s*(\w+)?', line)
                if match:
                    timestamp_ns = match.group(1)
                    current_value = int(match.group(3))
                    
                    # Calculate incremental value (difference from previous)
                    if previous_value is not None:
                        incremental_value = current_value - previous_value
                        # Handle potential counter resets or negative values
                        if incremental_value < 0:
                            incremental_value = current_value
                    else:
                        # First data point, incremental value is None
                        incremental_value = None
                    
                    previous_value = current_value
                    
                    # Only add to data if incremental_value is not None (skip first data point)
                    if incremental_value is not None:
                        data.append({
                            'timestamp_ns': timestamp_ns,
                            'value': str(incremental_value)
                        })
    
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        return 1
    
    # Write CSV output
    try:
        with open(output_file, 'w') as f:
            # Write CSV header
            f.write("timestamp_ns,pswpout_pages\n")
            
            # Write data rows
            for row in data:
                f.write(f"{row['timestamp_ns']},{row['value']}\n")
        
        print(f"Successfully converted {len(data)} records to '{output_file}'")
        return 0
    
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        return 1

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 pswpout_timestamped.py <input_directory> <output_directory>", file=sys.stderr)
        print("Example: python3 pswpout_timestamped.py /path/to/data /path/to/output_directory", file=sys.stderr)
        return 1
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Get the script name without extension
    rawdata_name = "pswpout_timestamped"
    
    # Construct the input file path (same name as script, without extension)
    input_file = os.path.join(input_dir, rawdata_name)
    output_file = os.path.join(output_dir, rawdata_name +".diff" + ".csv")
    
    return parse_timestamped_file(input_file, output_file)

if __name__ == "__main__":
    sys.exit(main())