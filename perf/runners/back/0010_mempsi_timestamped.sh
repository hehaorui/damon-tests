#!/bin/bash

while :
do
	# Get current time since boot using Python high-precision timer
	timestamp_ns=$(python3 -c "import time; print(time.clock_gettime_ns(time.CLOCK_BOOTTIME))")
	timestamp="[$timestamp_ns]"
	
	psi_mem_info=$(cat /proc/pressure/memory)
	
	echo "$timestamp $psi_mem_info" >> "$1/psi_mem_timestamped"
	
	sleep 0.1
done