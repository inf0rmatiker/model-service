#!/bin/bash

SCRIPT_DIR="$HOME/model-service/cluster-scripts/monitoring/free"

readarray -t HOSTS < "$SCRIPT_DIR/hosts.txt"
OUTPUT_DIR=$1
mkdir -p $OUTPUT_DIR

for HOST in ${HOSTS[@]}; do

  OUT_FILE="$HOME/memory_monitor/${HOST}_free.csv"
  if [[ "$HOST" == "$(hostname)" ]]; then
    pkill memory_monitor.sh
    mv "$OUT_FILE" "$OUTPUT_DIR/${HOST}_free.csv"
  else
    ssh "$HOST" "kill \$(ps -aux | grep memory_monitor.sh | awk '{print \$2}')"
  fi
done