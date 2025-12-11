#!/bin/bash

# Monitor the scheme quota effective_bytes of damon

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
scheme_quota_dir="$scheme_dir/quotas"
state_file="$sysfs_dir/state"

while :;
do
	# Get current time since boot using Python high-precision timer
	timestamp_ns=$(python3 -c "import time; print(time.clock_gettime_ns(time.CLOCK_BOOTTIME))")
	outfile="$odir/scheme_quota_timestamped"
	logline="[$timestamp_ns]"
	
	if [ -f "$state_file" ]
	then
		# Trigger update of schemes effective_bytes
		echo "update_schemes_effective_quotas" | \
      sudo tee "$state_file" > /dev/null
		
		if [ -d "$scheme_quota_dir" ]
		then
			# Read effective_bytes from the quota directory
			effective_bytes=$(sudo cat "$scheme_quota_dir/effective_bytes" 2>/dev/null)
			if [ -n "$effective_bytes" ]
			then
				logline+=" effective_bytes:$effective_bytes"
			else
				logline+=" effective_bytes:NA"
			fi
		else
			logline+=" wait for damon scheme quota directory"
		fi
	else
		logline+=" wait for damon state file"
	fi
	
	echo "$logline" >> "$outfile"
	sleep 0.1
done