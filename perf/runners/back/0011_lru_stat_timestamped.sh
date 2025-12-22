#!/bin/bash

while :
do
	active_mem=$(grep -m 1 "Active:" /proc/meminfo | awk '{print $2}')
	inactive_mem=$(grep -m 1 "Inactive:" /proc/meminfo | awk '{print $2}')
	active_anon_mem=$(grep -m 1 "Active(anon):" /proc/meminfo | awk '{print $2}')
	inactive_anon_mem=$(grep -m 1 "Inactive(anon):" /proc/meminfo | awk '{print $2}')
	active_file_mem=$(grep -m 1 "Active(file):" /proc/meminfo | awk '{print $2}')
	inactive_file_mem=$(grep -m 1 "Inactive(file):" /proc/meminfo | awk '{print $2}')
	
	# Get current time since boot using Python high-precision timer
	timestamp_ns=$(python3 -c "import time; print(time.clock_gettime_ns(time.CLOCK_BOOTTIME))")
	timestamp="[$timestamp_ns]"
	
	echo "$timestamp Active: $active_mem kB" >> "$1/active_mem_timestamped"
	echo "$timestamp Inactive: $inactive_mem kB" >> "$1/inactive_mem_timestamped"
	echo "$timestamp Active(anon): $active_anon_mem kB" >> "$1/active_anon_mem_timestamped"
	echo "$timestamp Inactive(anon): $inactive_anon_mem kB" >> "$1/inactive_anon_mem_timestamped"
	echo "$timestamp Active(file): $active_file_mem kB" >> "$1/active_file_mem_timestamped"
	echo "$timestamp Inactive(file): $inactive_file_mem kB" >> "$1/inactive_file_mem_timestamped"
	
	sleep 0.1
done