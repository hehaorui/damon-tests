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
	# Get current time since boot using Python high-precision timer
	timestamp_ns=$(python3 -c "import time; print(time.clock_gettime_ns(time.CLOCK_BOOTTIME))")
	timestamp="[$timestamp_ns]"
	
	pid=`pidof $work`
	if [ $pid ]
	then
		mem_info=$(ps -o vsz=,rss=,pid=,cmd= --pid `pidof $work`)
		echo "$timestamp $mem_info" >> $1/memfps_timestamped
	fi
	sleep 0.1
done