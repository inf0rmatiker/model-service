#!/bin/bash

LOG_DIR="$HOME/memory_monitor"
LOG_FILE="$LOG_DIR/$(hostname)_free.csv"
mkdir -p $LOG_DIR

echo "timestamp,total,used,free,shared,buff/cache,available" > $LOG_FILE

i=0
while true; do
  LINE=$(free --mega | grep "Mem")
  STR_ARRAY=($LINE)
  echo -e "$i,${STR_ARRAY[1]},${STR_ARRAY[2]},${STR_ARRAY[3]},${STR_ARRAY[4]},${STR_ARRAY[5]},${STR_ARRAY[6]}" >> $LOG_FILE
  let i++
  sleep 1
done