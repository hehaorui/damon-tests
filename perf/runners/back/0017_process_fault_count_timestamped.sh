#!/bin/bash
# SPDX-License-Identifier: GPL-2.0

ODIR=$1
work=$(basename $(dirname $(dirname $ODIR)))
work_category=$(basename $(dirname $(dirname $(dirname $ODIR))))
if [ "$work_category" = "parsec3" ] && [ "$work" = "raytrace" ]
then
	work="rtview"
elif [ "$work_category" = "ycsb" ]
then
	work="dbtest"
elif [ "$work_category" = "mysql" ]
then
	work="mysqld"
fi

while true;
do
	pid=`pidof $work`
	if [ $pid ]
	then
		# Get page fault information from /proc/[pid]/stat
		# Field 10: minflt (minor page faults)
		# Field 12: majflt (major page faults)
		stat_info=$(cat /proc/$pid/stat)
		minflt=$(echo $stat_info | awk '{print $10}')
		majflt=$(echo $stat_info | awk '{print $12}')
		
		# Get current time since boot using Python high-precision timer
		timestamp_ns=$(python3 -c "import time; print(time.clock_gettime_ns(time.CLOCK_BOOTTIME))")
		timestamp="[$timestamp_ns]"
	
		echo "$timestamp minflt: $minflt majflt: $majflt" >> "$1/process_fault_count_timestamped"
	fi
	sleep 0.1
done
