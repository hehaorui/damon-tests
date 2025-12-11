#!/bin/bash

# Monitor zhe scheme statistics of damon

# $1: <...>/results/<exp>/<variance>/0(0-9)
if [ "$EUID" -ne 0 ]
then
	echo "run as root"
	exit 1
fi

if [ $# -ne 1 ]
then
	echo "Usage: $0 <output dir>"
	exit 1
fi

if [ "$var" = "orig" ] || [ "$var" = "thp" ] || [ "$var" = "ttmo" ] || \
	[ "$var" = "rec" ] || [ "$var" = "prec" ]
then
	exit 0
fi

bindir=$(dirname "$0")
odir=$1
var=$(basename $(dirname "$odir"))
work=$(basename $(dirname $(dirname $odir)))
work_category=$(basename $(dirname $(dirname $(dirname $odir))))

sysfs_dir="/sys/kernel/mm/damon/admin/kdamonds/0/"
schemes_dir="$sysfs_dir/contexts/0/schemes"
scheme_dir="$sysfs_dir/contexts/0/schemes/0"
scheme_stat_dir="$scheme_dir/stats"
stats="nr_tried sz_tried nr_applied sz_applied qt_exceeds"

while :;
do
	# Get current time since boot using Python high-precision timer
	timestamp_ns=$(python3 -c "import time; print(time.clock_gettime_ns(time.CLOCK_BOOTTIME))")
	outfile="$odir/scheme_stats_timestamped"
	logline="[$timestamp_ns]"
	if [ -d "$scheme_stat_dir" ]
	then
		echo update_schemes_stats | sudo tee "$sysfs_dir/state" > /dev/null
		for s in $stats
		do
			val=$(sudo cat "$scheme_stat_dir/$s")
			logline+=" $s:$val"
		done
	else
		logline+=" wait for damon scheme directory"
	fi
		echo "$logline" >> "$outfile"
		sleep 0.1
done
