#!/bin/bash

OUT_DIR="$HOME/memory_monitor"

SCRIPT_DIR="$HOME/model-service/cluster_scripts/monitoring/free"
readarray -t HOSTS < "$SCRIPT_DIR/hosts.txt"

for HOST in ${HOSTS[@]}; do
  if [[ "$HOST" == "$(hostname)" ]]; then
    nohup "$SCRIPT_DIR/memory_monitor.sh" & disown
  else
    nohup ssh "$HOST" "$SCRIPT_DIR/memory_monitor.sh" & disown
  fi
done