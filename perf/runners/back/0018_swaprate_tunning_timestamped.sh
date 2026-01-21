#!/bin/bash

# Do feedback-based quota autotune for "my_prcl_rss*" variants.

# $1: <...>/results/<exp>/<variance>/0(0-9)
bindir=$(dirname "$0")
odir=$1
var=$(basename $(dirname "$odir"))
work=$(basename $(dirname $(dirname $odir)))
work_category=$(basename $(dirname $(dirname $(dirname $odir))))

if  echo "$var" | grep "my_prcl_swaprate" --quiet
then
	# var names are my_prcl_swaprate_<goal_percent>_cold_<cold_threshold_ms>ms
	swaprate_goal_percent=$(echo "$var" | cut -d'_' -f4)
	if [ "$swaprate_goal_percent" = "" ]
	then
		swaprate_goal_percent=10
	fi
	# Convert goal from percent to bp (1 bp = 0.01%)
	swaprate_goal_bp=$((swaprate_goal_percent * 100))
	do_tuning=1
else
	do_tuning=0
fi


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


sysfs_dir="/sys/kernel/mm/damon/admin/kdamonds/0/"
goals_dir="$sysfs_dir/contexts/0/schemes/0/quotas/goals/"
goal_dir="$sysfs_dir/contexts/0/schemes/0/quotas/goals/0"

while :;
do
	outfile="$odir/swaprate_tuning_timestamped"
	logline=""

	pid=$(pidof $work)

	if [ $pid ]
	then
		# Read RSS and VmSwap from /proc/[pid]/status
		status_file="/proc/$pid/status"
		if [ -f "$status_file" ]
		then
			# Get RSS in KB (from VmRSS line)
			rss_kb=$(grep "^VmRSS:" "$status_file" | awk '{print $2}')
			# Get VmSwap in KB (from VmSwap line)
			vmswap_kb=$(grep "^VmSwap:" "$status_file" | awk '{print $2}')
			
			# Calculate swaprate as vmswap/(rss+vmswap) * 100, then convert to bp (1 bp = 0.01%)
			if [ -n "$rss_kb" ] && [ -n "$vmswap_kb" ] && [ "$((rss_kb + vmswap_kb))" -gt 0 ]
			then
				swaprate_now_bp=$((vmswap_kb * 10000 / (rss_kb + vmswap_kb)))
			else
				swaprate_now_bp=0
			fi
		else
			swaprate_now_percent=0
		fi
		
		if [ $do_tuning -eq 1 ]
		then
			if [ ! -d "$goal_dir" ]
			then
				echo 1 > "$goals_dir/nr_goals"
			fi
			echo "user_input" > "$goal_dir/target_metric"
			# when the current value is larger than goal, damon will decrease the quota
			# to reduce the rss, and vice versa, so we set the current value to the goal
			# to make damon adjust the quota to reach the goal.
			echo "$swaprate_goal_bp" > "$goal_dir/target_value"
			echo "$swaprate_now_bp" > "$goal_dir/current_value"
			echo commit_schemes_quota_goals > "$sysfs_dir/state"
			logline+="swaprate_bp:$swaprate_now_bp swaprate_goal_bp:$swaprate_goal_bp"
		else
			logline+="swaprate_bp:$swaprate_now_bp swaprate_goal_bp:N/A"
		fi		
	else
		logline+="no_process_found"
	fi
		# Get current time since boot using Python high-precision timer
		timestamp_ns=$(python3 -c "import time; print(time.clock_gettime_ns(time.CLOCK_BOOTTIME))")
		echo "[$timestamp_ns] $logline" >> "$outfile"
		sleep 1
done
