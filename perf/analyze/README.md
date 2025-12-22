# DAMON Data Analysis Tool

This directory contains tools for analyzing DAMON (Data Access Monitor) performance data from multiple directories.

## Key Features

- **MAJFLT-RSS Relationship Analysis**: Generates plots showing the relationship between major fault rates and RSS sizes
- **Multi-Directory Comparison**: Compares data from all input directories in a single plot with color coding
- **Automatic Data Extraction**: Intelligently extracts RSS and major fault data from various CSV files
- **Statistical Processing**: Calculates per-second fault rates for accurate analysis

## analyze.sh

A bash wrapper script that simplifies process of analyzing DAMON data using configuration files and generates MAJFLT-RSS relationship plots.

## _do_analyze.py

A Python script that extracts RSS and major fault data from multiple DAMON test directories and generates visualizations for analysis.

### Features

- **Configuration-driven**: Uses config files to define experiments and variants
- **Automatic path discovery**: Automatically finds input directories based on configuration
- **Parsed directory support**: Specifically looks for CSV files in `parsed/` subdirectories
- **Environment variable support**: Accepts config file path via CFG environment variable

### Usage

```bash
CFG=<config_file> ./analyze.sh
```

#### Example with custom_config.sh

```bash
CFG=../custom_config.sh ./analyze.sh
```

### Configuration Format

The config file should define:
- `EXPERIMENTS`: Base path to the experiments directory
- `VARIANTS`: Space-separated list of variant names
- `REPEATS`: Number of experiment repeats (optional)

Example config:
```bash
EXPERIMENTS="/path/to/damon-tests/perf"
VARIANTS="splash2x/ocean_cp/my_prcl_rss_409600_cold_500ms splash2x/ocean_cp/my_prcl_rss_819200_cold_1000ms"
REPEATS=1
```

### Expected Directory Structure

The script expects data in the following structure:

```
EXPERIMENTS/results/
├── <workload>/<variant>/
│   ├── 0/parsed/
│   │   ├── damon_data.csv
│   │   ├── memfps_timestamped.csv
│   │   ├── pgfaults_timestamped.csv
│   │   └── ... (other CSV files)
│   ├── 1/parsed/
│   └── ...
└── ...
```

## _do_analyze.py

A Python script that integrates CSV data from multiple DAMON test directories, handling time-stamp alignment across different sampling frequencies.

### Features

- **Multi-directory support**: Process data from multiple test directories simultaneously
- **Direct CSV processing**: Finds and processes all CSV files directly in specified directories (no subdirectory search)
- **Time-stamp alignment**: Integrates data with different sampling frequencies
- **Special handling for damon_data.csv**: Processes memory region data with proper timestamp conversion
- **Metadata generation**: Creates detailed metadata about processed files and data structures

### Usage

```bash
python _do_analyze.py <output_directory> <input_directory1> [input_directory2] ...
```

#### Examples

**Using the analyze.sh wrapper (recommended):**

```bash
# Using custom config file
CFG=../custom_config.sh ./analyze.sh

# This will:
# 1. Load configuration from custom_config.sh
# 2. Find all variant directories
# 3. Process each variant's 0/parsed/ directory
# 4. Generate integrated datasets for each variant
# 5. Save results to analyze/ directory
```

**Using _do_analyze.py directly:**

```bash
# Single directory analysis
python _do_analyze.py /tmp/analysis_output /path/to/damon/test/data/parsed

# Multiple directory analysis
python _do_analyze.py /tmp/multi_analysis /path/to/test1/parsed /path/to/test2/parsed /path/to/test3/parsed
```

### Input Data Structure

The analyze.sh wrapper expects CSV files in `parsed/` subdirectories:

```
<input_directory>/parsed/
├── damon_data.csv
├── memfps_timestamped.csv
├── pgfaults_timestamped.csv
├── pswpin_timestamped.diff.csv
├── kdamond_cpu_usage_timestamped.csv
├── rss_tuning_timestamped.csv
├── memavail_timestamped.csv
├── swapcached_timestamped.csv
├── psi_mem_timestamped.csv
└── ... (other CSV files)
```

**Important Notes**:
- The script processes **only CSV files** (.csv extension)
- Files with other extensions (.avg, .txt, etc.) are automatically skipped
- The analyze.sh wrapper specifically looks for `parsed/` subdirectories within each variant directory
- Each variant can have multiple numbered runs (0, 1, 2, etc.)

### Supported CSV File Types

1. **damon_data.csv**: Memory region data with start/end timestamps and region metrics
2. **timestamped_metrics**: Files with `timestamp_ns` as first column and various metrics
3. **single_value**: Files like `rss.avg` containing single numeric values

### Output Files

The analyze.sh wrapper generates the following files in the analyze/ directory:

1. **majflt_rss_relationship.png**: Main analysis plot showing:
   - RSS size vs major fault rate relationship
   - Different colors for different input directories
   - Scatter plot with proper legends and labels
2. **analysis_metadata.json**: Detailed metadata including:
   - Input directories processed
   - File structures detected
   - Plot summary statistics
   - RSS and MAJFLT data counts

**When using _do_analyze.py directly:**

1. **integrated_timestamped_data.csv**: Single combined dataset with all timestamped data aligned by timestamps
2. **analysis_metadata.json**: Detailed metadata including:
   - Input directories processed
   - File structures detected
   - Data summary statistics

### Data Processing Pipeline

1. **Directory Discovery**: Analyze.sh discovers all variant directories from configuration
2. **Data Extraction**: _do_analyze.py extracts RSS and major fault data from CSV files:
   - RSS data: Extracts RSS/vsz values from appropriate CSV files
   - MAJFLT data: Extracts major fault counts and calculates per-second rates
3. **Visualization**: Creates scatter plots with:
   - X-axis: RSS size in MB
   - Y-axis: Major fault rate per second
   - Color coding: Different colors for each input directory
4. **Statistical Processing**: 
   - Converts major fault counts to rates per second
   - Handles time alignment and missing data
   - Provides source tracking for data provenance

### Dependencies

- Python 3.6+
- pandas
- numpy

### Example Output

**Using analyze.sh with custom_config.sh:**

```
Loading config from: ../custom_config.sh
EXPERIMENTS: /home/andy/workspaces/damon-tests/perf
VARIANTS: splash2x/ocean_cp/my_prcl_rss_409600_cold_500ms splash2x/ocean_cp/my_prcl_rss_819200_cold_1000ms ...
Total input directories found: 42

=== Extracting RSS and MAJFLT Data ===

--- Processing Directory 1: /home/andy/workspaces/damon-tests/perf/results/splash2x/ocean_cp/my_prcl_rss_409600_cold_500ms/01/parsed ---
  Extracted RSS data from rss_tuning_timestamped.csv: 1567 points
  Extracted MAJFLT data from pgmajfaults_timestamped.diff.csv: 2144 points

--- Processing Directory 2: /home/andy/workspaces/damon-tests/perf/results/splash2x/ocean_cp/my_prcl_rss_819200_cold_1000ms/01/parsed ---
  Extracted RSS data from rss_tuning_timestamped.csv: 1627 points
  Extracted MAJFLT data from pgmajfaults_timestamped.diff.csv: 1792 points
...

  Extracted RSS data from 42 directories
  Extracted MAJFLT data from 42 directories
Total RSS points: 68,432
Total MAJFLT points: 52,123

Saved plot: majflt_rss_relationship.png

Analysis complete!
Results saved to: /home/andy/workspaces/damon-tests/perf/analyze
Plot saved to: /home/andy/workspaces/damon-tests/perf/analyze/majflt_rss_relationship.png
Metadata saved to: /home/andy/workspaces/damon-tests/perf/analyze/analysis_metadata.json
```

**Using _do_analyze.py directly:**

```
Output directory: /tmp/test_output
--- Input Directory 1: /path/to/data ---
Found 22 CSV files
  damon_data.csv: damon_data
  memfps_timestamped.csv: timestamped_metrics
  pgfaults_timestamped.csv: timestamped_metrics
  ...

=== Integrating Data ===
Found 1 damon_data files
Found 22 timestamped dataframes
Saved integrated data to /tmp/test_output/integrated_timestamped_data.csv
Integrated dataset shape: (32372, 4038)

Analysis complete!
Results saved to: /tmp/test_output
```

### Notes

**For analyze.sh wrapper:**
- The script automatically looks for CSV files in `parsed/` subdirectories
- Each variant generates a separate integrated dataset file
- Output files are named using the directory/variant name for easy identification
- The script processes all numbered runs (0, 1, 2, etc.) for each variant

**For _do_analyze.py:**
- Large datasets may generate significant output files (hundreds of MB)
- Memory region data from damon_data.csv can create wide datasets (4000+ columns)
- All timestamps are handled as nanoseconds for precision

**General:**
- CSV files with `.avg` extension are ignored (not CSV format)
- Only files with `.csv` extension are processed
- Each directory is processed independently (no cross-directory data mixing)