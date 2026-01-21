#!/usr/bin/env python3

import sys
import os
import re

def parse_timestamped_file(input_file, output_file):
    """
    Parse timestamped PSI memory data file and convert to CSV format with incremental values.
    
    Args:
        input_file: Path to the input timestamped file
        output_file: Path to the output CSV file
    """
    data = []
    previous_psi_some = None
    previous_psi_full = None
    
    try:
        with open(input_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # Parse line format: [timestamp_ns] some ... full ...
                # Extract timestamp
                timestamp_match = re.match(r'\[(\d+)\]\s+(.+)', line)
                if not timestamp_match:
                    continue
                    
                timestamp_ns = timestamp_match.group(1)
                psi_info = timestamp_match.group(2)
                
                # Parse PSI memory information
                psi_data = {'timestamp_ns': timestamp_ns}
                
                # Parse some pressure (memory stalls)
                some_match = re.search(r'some\s+avg10=([\d.]+)\s+avg60=([\d.]+)\s+avg300=([\d.]+)\s+total=(\d+)', psi_info)
                if some_match:
                    some_total = int(some_match.group(4))
                    psi_data['some_avg10'] = some_match.group(1)
                    psi_data['some_avg60'] = some_match.group(2)
                    psi_data['some_avg300'] = some_match.group(3)
                    psi_data['some_total'] = some_match.group(4)
                    
                    # Calculate incremental some_total
                    if previous_psi_some is not None:
                        incremental_some = some_total - previous_psi_some
                        if incremental_some < 0:
                            incremental_some = some_total
                    else:
                        incremental_some = None
                    
                    previous_psi_some = some_total
                    psi_data['some_increment'] = str(incremental_some) if incremental_some is not None else ''
                
                # Parse full pressure (memory stalls)
                full_match = re.search(r'full\s+avg10=([\d.]+)\s+avg60=([\d.]+)\s+avg300=([\d.]+)\s+total=(\d+)', psi_info)
                if full_match:
                    full_total = int(full_match.group(4))
                    psi_data['full_avg10'] = full_match.group(1)
                    psi_data['full_avg60'] = full_match.group(2)
                    psi_data['full_avg300'] = full_match.group(3)
                    psi_data['full_total'] = full_match.group(4)

                    # Calculate incremental full_total
                    if previous_psi_full is not None:
                        incremental_full = full_total - previous_psi_full
                        if incremental_full < 0:
                            incremental_full = full_total
                    else:
                        incremental_full = None
                    
                    previous_psi_full = full_total
                    psi_data['full_increment'] = str(incremental_full) if incremental_full is not None else ''
                
                # Only add if we found some pressure data
                if 'some_avg10' in psi_data:
                    data.append(psi_data)
    
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
            f.write("timestamp_ns,some_avg10,some_avg60,some_avg300,some_total,some_increment,full_avg10,full_avg60,full_avg300,full_total,full_increment\n")
            
            # Write data rows
            for row in data:
                f.write(f"{row['timestamp_ns']},"
                        f"{row.get('some_avg10', '')},{row.get('some_avg60', '')},{row.get('some_avg300', '')},"
                        f"{row.get('some_total', '')},{row.get('some_increment', '')},"
                        f"{row.get('full_avg10', '')},{row.get('full_avg60', '')},{row.get('full_avg300', '')},"
                        f"{row.get('full_total', '')},{row.get('full_increment', '')}\n")
        
        print(f"Successfully converted {len(data)} records to '{output_file}'")
        return 0
    
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        return 1

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 psi_mem_timestamped.py <input_directory> <output_directory>", file=sys.stderr)
        print("Example: python3 psi_mem_timestamped.py /path/to/data /path/to/output_directory", file=sys.stderr)
        return 1
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Get the script name without extension
    rawdata_name = "psi_mem_timestamped"
    
    # Construct the input file path (same name as script, without extension)
    input_file = os.path.join(input_dir, rawdata_name)
    output_file = os.path.join(output_dir, rawdata_name + ".csv")
    
    return parse_timestamped_file(input_file, output_file)

if __name__ == "__main__":
    sys.exit(main())