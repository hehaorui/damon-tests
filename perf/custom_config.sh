#!/bin/bash
# SPDX-License-Identifier: GPL-2.0

EXPERIMENTS=`dirname $BASH_SOURCE`

# parsec_workloads="blackscholes bodytrack canneal dedup facesim "
# parsec_workloads+="fluidanimate freqmine raytrace streamcluster swaptions "
# parsec_workloads+="vips"
parsec_workloads=""

#splash2x_workloads="barnes fft lu_cb lu_ncb ocean_cp radiosity "
splash2x_workloads=""
# splash2x_workloads+="radix raytrace volrend water_nsquared water_spatial"
splash2x_workloads+="ocean_cp"

workloads=""
for w in $parsec_workloads
do
	workloads+="parsec3/$w "
done

for w in $splash2x_workloads
do
	workloads+=" splash2x/$w"
done

# vars="orig rec prec thp ethp prcl_auto_50 pdarc_v4_2_2 ttmo plrus_auto_7000"
# rss_goals_KB="$((400*1024)) $((500*1024)) \
# 							$((600*1024)) $((700*1024)) \
# 							$((800*1024)) $((900*1024)) \
# 							$((1000*1024))"

# the rate is calculated by (swapped_bytes)/(rss_bytes + swapped_bytes) * 100%
swaprate_goals_percents="10 15 20"

cold_thresholds_ms="500 1500 2500"
vars=""

for goal in $rss_goals_KB
do
	for cold_threshold in $cold_thresholds_ms
	do
		vars+="my_prcl_rss_${goal}_cold_${cold_threshold}ms "
	done
done

for goal in $swaprate_goals_percents
do
	for cold_threshold in $cold_thresholds_ms
	do
		vars+="my_prcl_swaprate_${goal}_cold_${cold_threshold}ms "
	done
done

# vars="prcl_auto_50"

VARIANTS=""

for v in $vars
do
	for w in $workloads
	do
		VARIANTS+="$w/$v "
	done
done

EXPERIMENTS=$EXPERIMENTS
VARIANTS=$VARIANTS
REPEATS=1
