#!/usr/bin/env python3

import sys
import os
import re

def parse_timestamped_file(input_file, output_file):
    """
    Parse timestamped RSS tuning data file and convert to CSV format.
    
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
                
                # Parse line format: [timestamp_ns] rss:$rss_now_KB rss_goal:$rss_goal_KB
                # or: [timestamp_ns] rss:$rss_now_KB rss_goal:N/A
                # or: [timestamp_ns] no_process_found
                
                # Extract timestamp
                timestamp_match = re.match(r'\[(\d+)\]\s+(.+)', line)
                if not timestamp_match:
                    continue
                    
                timestamp_ns = timestamp_match.group(1)
                log_info = timestamp_match.group(2)
                
                # Parse RSS tuning information
                tuning_data = {'timestamp_ns': timestamp_ns}
                
                if 'no_process_found' in log_info:
                    # No process found case - skip this line
                    continue
                else:
                    # Extract RSS value
                    rss_match = re.search(r'rss:(\d+)', log_info)
                    if rss_match:
                        tuning_data['rss_KB'] = rss_match.group(1)
                    else:
                        tuning_data['rss_KB'] = ''
                    
                    # Extract RSS goal
                    rss_goal_match = re.search(r'rss_goal:(\d+)', log_info)
                    if rss_goal_match:
                        tuning_data['rss_goal_KB'] = rss_goal_match.group(1)
                    elif 'rss_goal:N/A' in log_info:
                        tuning_data['rss_goal_KB'] = 'N/A'
                    else:
                        tuning_data['rss_goal_KB'] = ''
                
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
            f.write("timestamp_ns,rss_KB,rss_goal_KB\n")
            
            # Write data rows
            for row in data:
                rss_kb = row.get('rss_KB', '')
                rss_goal_kb = row.get('rss_goal_KB', '')
                
                f.write(f"{row['timestamp_ns']},{rss_kb},{rss_goal_kb}\n")
        
        print(f"Successfully converted {len(data)} records to '{output_file}'")
        return 0
    
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        return 1

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 rss_tuning_timestamped.py <input_directory> <output_directory>", file=sys.stderr)
        print("Example: python3 rss_tuning_timestamped.py /path/to/data /path/to/output_directory", file=sys.stderr)
        return 1
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Get the script name without extension
    rawdata_name = "rss_tuning_timestamped"
    
    # Construct the input file path (same name as script, without extension)
    input_file = os.path.join(input_dir, rawdata_name)
    output_file = os.path.join(output_dir, rawdata_name + ".csv")
    
    return parse_timestamped_file(input_file, output_file)

if __name__ == "__main__":
    sys.exit(main())