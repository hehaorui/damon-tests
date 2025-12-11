#!/usr/bin/env python3

import sys
import os
import re

def parse_timestamped_file(input_file, output_file):
    """
    Parse timestamped process fault count data file and convert to CSV format with incremental values.
    
    Args:
        input_file: Path to the input timestamped file
        output_file: Path to the output CSV file
    """
    data = []
    previous_minflt = None
    previous_majflt = None
    
    try:
        with open(input_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Parse line format: [timestamp_ns] minflt: value majflt: value
                timestamp_match = re.match(r'\[(\d+)\]\s+minflt:\s+(\d+)\s+majflt:\s+(\d+)', line)
                if not timestamp_match:
                    continue
                
                timestamp_ns = timestamp_match.group(1)
                current_minflt = int(timestamp_match.group(2))
                current_majflt = int(timestamp_match.group(3))
                
                # Calculate incremental values (difference from previous)
                if previous_minflt is not None and previous_majflt is not None:
                    incremental_minflt = current_minflt - previous_minflt
                    incremental_majflt = current_majflt - previous_majflt
                    
                    # Handle potential counter resets or negative values
                    if incremental_minflt < 0:
                        incremental_minflt = current_minflt
                    if incremental_majflt < 0:
                        incremental_majflt = current_majflt
                else:
                    # First data point, skip it
                    previous_minflt = current_minflt
                    previous_majflt = current_majflt
                    continue
                
                previous_minflt = current_minflt
                previous_majflt = current_majflt
                
                data.append({
                    'timestamp_ns': timestamp_ns,
                    'minflt_count': str(incremental_minflt),
                    'majflt_count': str(incremental_majflt)
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
            f.write("timestamp_ns,minflt_count,majflt_count\n")
            
            # Write data rows
            for row in data:
                f.write(f"{row['timestamp_ns']},{row['minflt_count']},{row['majflt_count']}\n")
        
        print(f"Successfully converted {len(data)} records to '{output_file}'")
        return 0
    
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        return 1

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 process_fault_count_timestamped.py <input_directory> <output_directory>", file=sys.stderr)
        print("Example: python3 process_fault_count_timestamped.py /path/to/data /path/to/output_directory", file=sys.stderr)
        return 1
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Get the script name without extension
    rawdata_name = "process_fault_count_timestamped"
    
    # Construct the input file path (same name as script, without extension)
    input_file = os.path.join(input_dir, rawdata_name)
    output_file = os.path.join(output_dir, rawdata_name +".diff" + ".csv")
    
    return parse_timestamped_file(input_file, output_file)

if __name__ == "__main__":
    sys.exit(main())