#!/bin/bash
# SPDX-License-Identifier: GPL-2.0
# Script to integrate timestamped CSV data to 100ms grid and collect statistics

if [ $# -lt 2 ]
then
    echo "Usage: $0 <output directory> <src directory [src directory ...]>"
    exit 1
fi

# Output directory for statistics files
ODIR=$1
SDIR=${@:2}

# Call Python script for each parsed directory
for d in $SDIR
do
    if [ -d "$d" ]; then
        python3 "$(dirname "$0")/_integrated_data.py" "$d"
    fi
done

# # After data integration, collect majflt_count and swaprate_bp statistics
# python3 "$(dirname "$0")/_majflt_swaprate.py" "$ODIR" $SDIR

# # Collect psi_mem_increment and swaprate_bp statistics
# python3 "$(dirname "$0")/_psi_swaprate.py" "$ODIR" $SDIR
