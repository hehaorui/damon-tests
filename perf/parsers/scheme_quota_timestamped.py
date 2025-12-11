#!/usr/bin/env python3

import sys
import os
import re

def parse_timestamped_file(input_file, output_file):
    """
    Parse timestamped scheme quota data file and convert to CSV format.
    
    Args:
        input_file: Path to the input timestamped file
        output_file: Path to the output CSV file
    """
    data = []
    
    try:
        with open(input_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Parse line format: [timestamp_ns] effective_bytes:value
                # or: [timestamp_ns] effective_bytes:NA
                # or: [timestamp_ns] wait for damon state file
                # or: [timestamp_ns] wait for damon scheme quota directory
                
                # Extract timestamp
                timestamp_match = re.match(r'\[(\d+)\]\s+(.+)', line)
                if not timestamp_match:
                    continue
                    
                timestamp_ns = timestamp_match.group(1)
                quota_info = timestamp_match.group(2)
                
                # Skip lines with "wait for damon state file" or "wait for damon scheme quota directory"
                if 'wait for damon state file' in quota_info or 'wait for damon scheme quota directory' in quota_info:
                    continue
                
                # Parse scheme quota information
                quota_data = {'timestamp_ns': timestamp_ns}
                
                # Extract effective_bytes value
                effective_bytes_match = re.search(r'effective_bytes:(\d+)', quota_info)
                if effective_bytes_match:
                    quota_data['effective_bytes'] = effective_bytes_match.group(1)
                elif 'effective_bytes:NA' in quota_info:
                    # Skip lines with NA value
                    continue
                else:
                    quota_data['effective_bytes'] = ''
                
                # Only add if we found effective_bytes data
                if quota_data['effective_bytes'] != '':
                    data.append(quota_data)
    
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
            f.write("timestamp_ns,effective_bytes\n")
            
            # Write data rows
            for row in data:
                effective_bytes = row.get('effective_bytes', '')
                f.write(f"{row['timestamp_ns']},{effective_bytes}\n")
        
        print(f"Successfully converted {len(data)} records to '{output_file}'")
        return 0
    
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        return 1

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 scheme_quota_timestamped.py <input_directory> <output_directory>", file=sys.stderr)
        print("Example: python3 scheme_quota_timestamped.py /path/to/data /path/to/output_directory", file=sys.stderr)
        return 1
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Get script name without extension
    rawdata_name = "scheme_quota_timestamped"
    
    # Construct the input file path (same name as script, without extension)
    input_file = os.path.join(input_dir, rawdata_name)
    output_file = os.path.join(output_dir, rawdata_name + ".csv")
    
    return parse_timestamped_file(input_file, output_file)

if __name__ == "__main__":
    sys.exit(main())