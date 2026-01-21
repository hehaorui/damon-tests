#!/usr/bin/env python3

import sys
import os
import re

def parse_timestamped_file(input_file, output_file):
    """
    Parse timestamped swaprate tuning data file and convert to CSV format.
    
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
                
                # Parse line format: [timestamp_ns] swaprate_bp:$swaprate_now_bp swaprate_goal_bp:$swaprate_goal_bp
                # or: [timestamp_ns] swaprate_bp:$swaprate_now_bp swaprate_goal_bp:N/A
                # or: [timestamp_ns] no_process_found
                
                # Extract timestamp
                timestamp_match = re.match(r'\[(\d+)\]\s+(.+)', line)
                if not timestamp_match:
                    continue
                    
                timestamp_ns = timestamp_match.group(1)
                log_info = timestamp_match.group(2)
                
                # Parse swaprate tuning information
                tuning_data = {'timestamp_ns': timestamp_ns}
                
                if 'no_process_found' in log_info:
                    # No process found case - skip this line
                    continue
                else:
                    # Extract swaprate value
                    swaprate_match = re.search(r'swaprate_bp:(\d+)', log_info)
                    if swaprate_match:
                        tuning_data['swaprate_bp'] = swaprate_match.group(1)
                    else:
                        tuning_data['swaprate_bp'] = ''
                    
                    # Extract swaprate goal
                    swaprate_goal_match = re.search(r'swaprate_goal_bp:(\d+)', log_info)
                    if swaprate_goal_match:
                        tuning_data['swaprate_goal_bp'] = swaprate_goal_match.group(1)
                    elif 'swaprate_goal_bp:N/A' in log_info:
                        tuning_data['swaprate_goal_bp'] = 'N/A'
                    else:
                        tuning_data['swaprate_goal_bp'] = ''
                
                data.append(tuning_data)
    
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
            f.write("timestamp_ns,swaprate_bp,swaprate_goal_bp\n")
            
            # Write data rows
            for row in data:
                swaprate_bp = row.get('swaprate_bp', '')
                swaprate_goal_bp = row.get('swaprate_goal_bp', '')
                
                f.write(f"{row['timestamp_ns']},{swaprate_bp},{swaprate_goal_bp}\n")
        
        print(f"Successfully converted {len(data)} records to '{output_file}'")
        return 0
    
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        return 1

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 swaprate_timestamped.py <input_directory> <output_directory>", file=sys.stderr)
        print("Example: python3 swaprate_timestamped.py /path/to/data /path/to/output_directory", file=sys.stderr)
        return 1
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Get the script name without extension
    rawdata_name = "swaprate_tuning_timestamped"
    
    # Construct the input file path (same name as script, without extension)
    input_file = os.path.join(input_dir, rawdata_name)
    output_file = os.path.join(output_dir, rawdata_name + ".csv")
    
    return parse_timestamped_file(input_file, output_file)

if __name__ == "__main__":
    sys.exit(main())