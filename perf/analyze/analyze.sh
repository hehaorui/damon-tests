#!/bin/bash
# SPDX-License-Identifier: GPL-2.0

# Analyze script wrapper for _do_analyze.py
# Usage: CFG=custom_config.sh ./analyze.sh

set -e  # Exit on any error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/analyze_results"  # Output to the analyze_results directory

# Check if CFG environment variable is set
if [ -z "$CFG" ]; then
    echo "Error: CFG environment variable is not set"
    echo "Please set CFG to the path of the configuration file"
    exit 1
fi

# Check if the config file exists
if [ ! -f "$CFG" ]; then
    echo "Error: Config file '$CFG' not found"
    exit 1
fi

echo "Loading config from: $CFG"

# Source the config file to get variables
source "$CFG"

# Check if required variables are defined
if [ -z "$EXPERIMENTS" ] || [ -z "$VARIANTS" ]; then
    echo "Error: Required variables EXPERIMENTS or VARIANTS not found in config file"
    exit 1
fi

echo "EXPERIMENTS: $EXPERIMENTS"
echo "VARIANTS: $VARIANTS"

# Build input directory paths based on EXPERIMENTS and VARIANTS
# The expected directory structure is: results/<variant>/0 (or 0-9)
INPUT_DIRS=""

# Convert VARIANTS string to array for processing
variants_array=($VARIANTS)

for variant in "${variants_array[@]}"; do
    # Remove any trailing whitespace
    variant=$(echo "$variant" | xargs)
    
    if [ -n "$variant" ]; then
        # Look for result directories with this variant
        # We'll check for directories like results/<variant>/0, results/<variant>/1, etc.
        results_base="$EXPERIMENTS/results/$variant"
        
        if [ -d "$results_base" ]; then
            # Find all numbered subdirectories (0, 1, 2, etc.)
            for run_dir in "$results_base"/*; do
                if [ -d "$run_dir" ]; then
                    run_dirname=$(basename "$run_dir")
                    # Check if the directory name is a number (0-9)
                    if [[ "$run_dirname" =~ ^[0-9]+$ ]]; then
                        # Check if parsed subdirectory exists
                        parsed_dir="$run_dir/parsed"
                        if [ -d "$parsed_dir" ]; then
                            INPUT_DIRS="$INPUT_DIRS $parsed_dir"
                            echo "Found input directory: $parsed_dir"
                        fi
                    fi
                fi
            done
        else
            echo "Warning: Results directory not found: $results_base"
        fi
    fi
done

# Convert to array and remove duplicates
input_dirs_array=($INPUT_DIRS)
unique_input_dirs=($(printf "%s\n" "${input_dirs_array[@]}" | sort -u))

echo "Total input directories found: ${#unique_input_dirs[@]}"

if [ ${#unique_input_dirs[@]} -eq 0 ]; then
    echo "Error: No input directories found"
    echo "Expected structure: results/<variant>/[0-9]"
    exit 1
fi

# Prepare the command to run _do_analyze.py
ANALYZE_SCRIPT="$SCRIPT_DIR/_do_analyze.py"

if [ ! -f "$ANALYZE_SCRIPT" ]; then
    echo "Error: Analysis script '$ANALYZE_SCRIPT' not found"
    exit 1
fi

echo "Running analysis script..."
echo "Output directory: $OUTPUT_DIR"
echo "Input directories: ${unique_input_dirs[@]}"

# Call the Python script with all input directories
python3 "$ANALYZE_SCRIPT" "$OUTPUT_DIR" "${unique_input_dirs[@]}"

echo "Analysis completed successfully!"
