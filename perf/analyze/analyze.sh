#!/bin/bash
# SPDX-License-Identifier: GPL-2.0

# Analyze script wrapper for _do_analyze.py
# Usage: CFG=custom_config.sh ./analyze.sh

set -e  # Exit on any error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/analyze_results"  # Output to the analyze_results directory
MERGE_RESULTS_DIR="$SCRIPT_DIR/merge_results"  # Directory containing merged CSV files

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

# Check if merge_results directory exists
if [ ! -d "$MERGE_RESULTS_DIR" ]; then
    echo "Error: Merge results directory '$MERGE_RESULTS_DIR' not found"
    echo "Please run merge.sh first to generate integrated CSV files"
    exit 1
fi

echo "Looking for integrated CSV files in: $MERGE_RESULTS_DIR"

# Convert VARIANTS string to array for processing
variants_array=($VARIANTS)

# Scan all integrated CSV files in merge_results directory
# Build list of CSV files that match the variants
INPUT_FILES=""

if [ -d "$MERGE_RESULTS_DIR" ]; then
    for csv_file in "$MERGE_RESULTS_DIR"/integrated_*.csv; do
        if [ -f "$csv_file" ]; then
            # Extract variant name from filename
            # Filename format: integrated_<variant_name>.csv
            basename=$(basename "$csv_file")
            variant_name="${basename#integrated_}"
            variant_name="${variant_name%.csv}"
            
            # Check if this variant name matches any variant in VARIANTS
            matched=0
            for variant in "${variants_array[@]}"; do
                variant=$(echo "$variant" | xargs)
                if [ -n "$variant" ]; then
                    # Check if variant_name contains the variant string
                    # This handles cases where the full variant name may be extracted from directory paths
                    if [[ "$variant_name" == *"$variant"* ]] || [[ "$variant" == *"$variant_name"* ]]; then
                        INPUT_FILES="$INPUT_FILES $csv_file"
                        echo "Found integrated CSV: $csv_file (variant: $variant_name)"
                        matched=1
                        break
                    fi
                fi
            done
        fi
    done
else
    echo "Error: Merge results directory '$MERGE_RESULTS_DIR' not found"
    exit 1
fi

# Convert to array and remove duplicates
input_files_array=($INPUT_FILES)
unique_input_files=($(printf "%s\n" "${input_files_array[@]}" | sort -u))

echo "Total input CSV files found: ${#unique_input_files[@]}"

if [ ${#unique_input_files[@]} -eq 0 ]; then
    echo "Error: No input CSV files found"
    echo "Expected files in format: merge_results/integrated_<variant_name>.csv"
    echo "Please run merge.sh first to generate integrated CSV files"
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
echo "Input CSV files:"
for file in "${unique_input_files[@]}"; do
    echo "  - $file"
done

# Call the Python script with all input CSV files
python3 "$ANALYZE_SCRIPT" "$OUTPUT_DIR" "${unique_input_files[@]}"

echo "Analysis completed successfully!"
