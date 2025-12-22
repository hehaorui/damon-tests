#!/bin/bash
# SPDX-License-Identifier: GPL-2.0

while :
do
	memavail=$(cat /proc/meminfo | grep MemAvailable | awk '{print $2}')
	swapcached=$(cat /proc/meminfo | grep SwapCached | awk '{print $2}')
	pgfaults=$(grep pgfault /proc/vmstat | awk '{print $2}')
	pgmajfaults=$(grep pgmajfault /proc/vmstat | awk '{print $2}')
	
	# Get current time since boot using Python high-precision timer
	timestamp_ns=$(python3 -c "import time; print(time.clock_gettime_ns(time.CLOCK_BOOTTIME))")
	timestamp="[$timestamp_ns]"
	
	echo "$timestamp MemAvailable: $memavail kB" >> "$1/memavail_timestamped"
	echo "$timestamp SwapCached: $swapcached kB" >> "$1/swapcached_timestamped"
	echo "$timestamp pgfault: $pgfaults" >> "$1/pgfaults_timestamped"
	echo "$timestamp pgmajfault: $pgmajfaults" >> "$1/pgmajfaults_timestamped"
	
	sleep 0.1
done