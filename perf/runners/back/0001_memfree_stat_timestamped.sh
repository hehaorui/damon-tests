#!/bin/bash
# SPDX-License-Identifier: GPL-2.0

while :
do
	memfree=$(grep -m 1 MemFree /proc/meminfo | awk '{print $2}')
	nr_free_pages=$(grep -m 1 nr_free_pages /proc/vmstat | awk '{print $2}')
	
	# Get current time since boot using Python high-precision timer
	timestamp_ns=$(python3 -c "import time; print(time.clock_gettime_ns(time.CLOCK_BOOTTIME))")
	timestamp="[$timestamp_ns]"
	
	echo "$timestamp MemFree: $memfree kB" >> "$1/memfree_timestamped"
	echo "$timestamp nr_free_pages: $nr_free_pages" >> "$1/nr_free_pages_timestamped"
	
	sleep 0.1
done