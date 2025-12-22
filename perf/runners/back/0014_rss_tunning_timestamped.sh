#!/bin/bash

# Do feedback-based quota autotune for "my_prcl_rss*" variants.

# $1: <...>/results/<exp>/<variance>/0(0-9)
bindir=$(dirname "$0")
odir=$1
var=$(basename $(dirname "$odir"))
work=$(basename $(dirname $(dirname $odir)))
work_category=$(basename $(dirname $(dirname $(dirname $odir))))

if  echo "$var" | grep "my_prcl_rss" --quiet
then
	# var names are my_prcl_rss_<goal_KB>
	rss_goal_KB=$(echo "$var" | cut -d'_' -f4)
	if [ "$rss_goal_KB" = "" ]
	then
		rss_goal_KB=$((50*1024))
	fi
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
	# Get current time since boot using Python high-precision timer
	outfile="$odir/rss_tuning_timestamped"
	logline=""

	pid=$(pidof $work)

	if [ $pid ]
	then
		rss_now_KB=$(ps -o rss= -p $pid)
		
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
			echo "$rss_goal_KB" > "$goal_dir/current_value"
			echo "$rss_now_KB" > "$goal_dir/target_value"
			echo commit_schemes_quota_goals > "$sysfs_dir/state"
			logline+=" rss:$rss_now_KB rss_goal:$rss_goal_KB"
		else
			logline+=" rss:$rss_now_KB rss_goal:N/A"
		fi		
	else
		logline+=" no_process_found"
	fi
		timestamp_ns=$(python3 -c "import time; print(time.clock_gettime_ns(time.CLOCK_BOOTTIME))")
		echo "[$timestamp_ns]"+"$logline" >> "$outfile"
		sleep 1
done
