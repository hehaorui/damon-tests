#!/bin/bash
# SPDX-License-Identifier: GPL-2.0

rm -fr ./results
sudo /home/andy/workspaces/lazybox/tune/zram_swap.sh 4G
from_date=$(date)
time CFG=full_once_config.sh ./run.sh
echo "tests ran from $from_date to $(date)"
