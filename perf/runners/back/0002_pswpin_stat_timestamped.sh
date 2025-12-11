#!/bin/bash
# SPDX-License-Identifier: GPL-2.0

while :
do
	# Get current time since boot using Python high-precision timer
	timestamp_ns=$(python3 -c "import time; print(time.clock_gettime_ns(time.CLOCK_BOOTTIME))")
	timestamp="[$timestamp_ns]"
	
	pswpin_value=$(cat /proc/vmstat | grep pswpin | awk '{print $2}')
	
	echo "$timestamp pswpin: $pswpin_value" >> "$1/pswpin_timestamped"
	
	sleep 0.1
done