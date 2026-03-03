#!/usr/bin/env python3
"""
Generate memory heatmaps using damo for the first run of each workload/variant combination.

This script finds all damon.data files in the results directory and generates
heatmap visualizations using the damo tool for each variant's first run.
"""

import os
import subprocess
import sys
from pathlib import Path


def find_workload_variants(results_base):
    """
    Find all workload/variant combinations in the results directory.
    
    Returns:
        list: List of tuples (category, workload, variant) representing each combination
    """
    combinations = []
    results_path = Path(results_base)
    
    # Iterate through categories
    for category_dir in results_path.iterdir():
        if not category_dir.is_dir():
            continue
            
        category = category_dir.name
        
        # Iterate through workloads
        for workload_dir in category_dir.iterdir():
            if not workload_dir.is_dir():
                continue
                
            workload = workload_dir.name
            
            # Iterate through variants
            for variant_dir in workload_dir.iterdir():
                if not variant_dir.is_dir():
                    continue
                    
                variant = variant_dir.name
                combinations.append((category, workload, variant))
    
    return sorted(combinations)


def generate_heatmap_for_run(damo_path, damon_data_file, output_file):
    """
    Generate a heatmap for a single run using damo.
    
    Args:
        damo_path: Path to the damo script
        damon_data_file: Path to the damon.data file
        output_file: Path where the heatmap PNG will be saved
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        cmd = [
            sys.executable,
            str(damo_path),
            'report', 'heatmap',
            '--input', str(damon_data_file),
            '--output', str(output_file)
        ]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300  # 5 minutes timeout per heatmap
        )
        
        if result.returncode == 0 and os.path.exists(output_file):
            return True
        else:
            print(f"    Error generating heatmap: {result.stderr.decode('utf-8')}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"    Timeout generating heatmap after 5 minutes")
        return False
    except Exception as e:
        print(f"    Exception: {e}")
        return False


def generate_all_heatmaps(results_base, output_path, damo_path):
    """
    Generate heatmaps for the first run of each workload/variant combination.
    
    Args:
        results_base: Base directory of the collected results
        output_path: Directory where heatmaps will be saved
        damo_path: Path to the damo script (damo.py)
    """
    # Ensure output directory exists
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all workload/variant combinations
    combinations = find_workload_variants(results_base)
    
    print(f"=== Generating Heatmaps for {len(combinations)} Variants ===\n")
    
    success_count = 0
    total_count = len(combinations)
    
    for category, workload, variant in combinations:
        # Construct the path to the first run (run 01)
        run_dir = Path(results_base) / category / workload / variant / "01"
        
        # Check if run directory exists
        if not run_dir.exists():
            print(f"Skipping {category}/{workload}/{variant}: Run 01 not found")
            continue
        
        # Check for damon.data file
        damon_data_file = run_dir / "damon.data"
        if not damon_data_file.exists():
            print(f"Skipping {category}/{workload}/{variant}: damon.data not found")
            continue
        
        # Create output filename: include workload, category, and variant to avoid conflicts
        variant_safe_name = variant.replace("/", "_")
        workload_safe_name = workload.replace("/", "_")
        category_safe_name = category.replace("/", "_")
        output_file = output_dir / f"{category_safe_name}_{workload_safe_name}_{variant_safe_name}_run_01_heatmap.png"
        
        # Generate the heatmap
        print(f"Generating heatmap for {category}/{workload}/{variant}:")
        print(f"  Input: {damon_data_file}")
        print(f"  Output: {output_file.name}")
        
        if generate_heatmap_for_run(damo_path, damon_data_file, output_file):
            print(f"  ✓ Success ({output_file.stat().st_size / 1024:.1f} KB)")
            success_count += 1
        else:
            print(f"  ✗ Failed")
        print()
    
    print(f"=== Summary ===")
    print(f"Generated {success_count}/{total_count} heatmaps successfully")
    print(f"Output directory: {output_path}")


def main():
    """Main entry point for the script."""
    # Default paths
    script_dir = Path(__file__).parent
    default_results_base = script_dir.parent.parent / "perf" / "results-collect"
    default_output_path = script_dir
    default_damo_path = script_dir.parent.parent.parent / "damo" / "src" / "damo.py"
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        results_base = sys.argv[1]
    else:
        results_base = str(default_results_base)
    
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    else:
        output_path = str(default_output_path)
    
    if len(sys.argv) > 3:
        damo_path = sys.argv[3]
    else:
        damo_path = str(default_damo_path)
    
    # Verify damo.py exists
    if not Path(damo_path).exists():
        print(f"Error: damo.py not found at {damo_path}")
        print("Usage: python3 generate_heatmaps.py [results_base] [output_path] [damo_path]")
        sys.exit(1)
    
    print(f"Results base: {results_base}")
    print(f"Output path: {output_path}")
    print(f"Damo path: {damo_path}")
    print()
    
    # Generate all heatmaps
    generate_all_heatmaps(results_base, output_path, Path(damo_path))


if __name__ == "__main__":
    main()
