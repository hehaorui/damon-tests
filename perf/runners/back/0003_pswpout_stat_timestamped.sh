#!/bin/bash
# SPDX-License-Identifier: GPL-2.0

while :
do
	pswpout_value=$(cat /proc/vmstat | grep pswpout | awk '{print $2}')
	
	# Get current time since boot using Python high-precision timer
	timestamp_ns=$(python3 -c "import time; print(time.clock_gettime_ns(time.CLOCK_BOOTTIME))")
	timestamp="[$timestamp_ns]"
	
	echo "$timestamp pswpout: $pswpout_value" >> "$1/pswpout_timestamped"
	
	sleep 0.1
done