#!/usr/bin/env python3

import sys
import os
import re

def parse_timestamped_file(input_file, output_file):
    """
    Parse timestamped memory footprint (memfps) data file and convert to CSV format.
    
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
                
                # Parse line format: [timestamp_ns] vsz rss pid cmd...
                match = re.match(r'\[(\d+)\]\s+(\d+)\s+(\d+)\s+(\d+)\s+(.+)', line)
                if match:
                    timestamp_ns = match.group(1)
                    vsz = match.group(2)  # Virtual memory size in KB
                    rss = match.group(3)  # Resident set size in KB
                    pid = match.group(4)  # Process ID
                    cmd = match.group(5)  # Command line
                    
                    data.append({
                        'timestamp_ns': timestamp_ns,
                        'vsz': vsz,
                        'rss': rss,
                        'pid': pid,
                        'cmd': cmd
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
            f.write("timestamp_ns,vsz,rss,pid,cmd\n")
            
            # Write data rows
            for row in data:
                f.write(f"{row['timestamp_ns']},{row['vsz']},{row['rss']},{row['pid']},\"{row['cmd']}\"\n")
        
        print(f"Successfully converted {len(data)} records to '{output_file}'")
        return 0
    
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        return 1

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 memfps_timestamped.py <input_directory> <output_directory>", file=sys.stderr)
        print("Example: python3 memfps_timestamped.py /path/to/data /path/to/output_directory", file=sys.stderr)
        return 1
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Get the script name without extension
    rawdata_name = "memfps_timestamped"
    
    # Construct the input file path (same name as script, without extension)
    input_file = os.path.join(input_dir, rawdata_name)
    output_file = os.path.join(output_dir, rawdata_name + ".csv")
    
    return parse_timestamped_file(input_file, output_file)

if __name__ == "__main__":
    sys.exit(main())