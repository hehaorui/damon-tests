#!/bin/bash
INPUT_DIR=$1
OUTPUT_DIR=$2

touch "$OUTPUT_DIR/integrated_data"
echo "This is a pseudo file for enabling parsing and statistics processing." \
  > "$OUTPUT_DIR/integrated_data"
