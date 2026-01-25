#!/bin/bash
# SPDX-License-Identifier: GPL-2.0

# Script to plot relationships between metrics across workloads and variants
# Usage: ./plot_metrics.sh <results-collect-directory>

RESULTS_BASE="$1"

if [ -z "$RESULTS_BASE" ]; then
    echo "Error: Results directory not specified"
    echo "Usage: $0 <results-collect-directory>"
    exit 1
fi

if [ ! -d "$RESULTS_BASE" ]; then
    echo "Error: Results directory not found: $RESULTS_BASE"
    exit 1
fi

echo "Results base directory: $RESULTS_BASE"
echo "Automatically discovering all workload/variant combinations..."

# Call the Python script to create plots
SCRIPT_DIR="$(dirname "$0")"
python3 "$SCRIPT_DIR/_plot_metrics.py" "$RESULTS_BASE"
