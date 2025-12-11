#!/usr/bin/env python3

import sys
import os
import re

def parse_timestamped_file(input_file, output_file):
    """
    Parse timestamped scheme statistics data file and convert to CSV format with incremental values.
    
    Args:
        input_file: Path to the input timestamped file
        output_file: Path to the output CSV file
    """
    data = []
    previous_values = {
        'nr_tried': None,
        'sz_tried': None,
        'nr_applied': None,
        'sz_applied': None,
        'qt_exceeds': None
    }
    
    try:
        with open(input_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Parse line format: [timestamp_ns] stat1:value1 stat2:value2 ...
                # or: [timestamp_ns] wait for damon scheme directory
                
                # Extract timestamp
                timestamp_match = re.match(r'\[(\d+)\]\s+(.+)', line)
                if not timestamp_match:
                    continue
                    
                timestamp_ns = timestamp_match.group(1)
                stats_info = timestamp_match.group(2)
                
                # Skip lines with "wait for damon scheme directory"
                if 'wait for damon scheme directory' in stats_info:
                    continue
                
                # Parse scheme statistics
                stats_data = {'timestamp_ns': timestamp_ns}
                
                # Parse individual statistics (nr_tried, sz_tried, nr_applied, sz_applied, qt_exceeds)
                stats_to_parse = ['nr_tried', 'sz_tried', 'nr_applied', 'sz_applied', 'qt_exceeds']
                
                for stat in stats_to_parse:
                    stat_match = re.search(rf'{stat}:(\d+)', stats_info)
                    if stat_match:
                        current_value = int(stat_match.group(1))
                        
                        # Calculate incremental value (difference from previous)
                        if previous_values[stat] is not None:
                            incremental_value = current_value - previous_values[stat]
                            # Handle potential counter resets or negative values
                            if incremental_value < 0:
                                # Counter reset detected, use current value as incremental
                                incremental_value = current_value
                        else:
                            # First data point, skip it
                            incremental_value = None
                        
                        if incremental_value is not None:
                            stats_data[stat] = str(incremental_value)
                        else:
                            stats_data[stat] = ''
                        
                        # Update previous value
                        previous_values[stat] = current_value
                    else:
                        stats_data[stat] = ''
                
                # Only add if we found at least one statistic
                if any(stats_data[stat] != '' for stat in stats_to_parse):
                    data.append(stats_data)
    
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
            f.write("timestamp_ns,nr_tried,sz_tried,nr_applied,sz_applied,qt_exceeds\n")
            
            # Write data rows
            for row in data:
                nr_tried = row.get('nr_tried', '')
                sz_tried = row.get('sz_tried', '')
                nr_applied = row.get('nr_applied', '')
                sz_applied = row.get('sz_applied', '')
                qt_exceeds = row.get('qt_exceeds', '')
                
                f.write(f"{row['timestamp_ns']},{nr_tried},{sz_tried},{nr_applied},{sz_applied},{qt_exceeds}\n")
        
        print(f"Successfully converted {len(data)} records to '{output_file}'")
        return 0
    
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        return 1

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 scheme_stats_timestamped.py <input_directory> <output_directory>", file=sys.stderr)
        print("Example: python3 scheme_stats_timestamped.py /path/to/data /path/to/output_directory", file=sys.stderr)
        return 1
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Get the script name without extension
    rawdata_name = "scheme_stats_timestamped"
    
    # Construct the input file path (same name as script, without extension)
    input_file = os.path.join(input_dir, rawdata_name)
    output_file = os.path.join(output_dir, rawdata_name +".diff" + ".csv")
    
    return parse_timestamped_file(input_file, output_file)

if __name__ == "__main__":
    sys.exit(main())