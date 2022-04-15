#!/bin/bash

function print_usage {
  echo -e "./kill_master.sh"
  echo -e "\tDESCRIPTION Shuts down the Master node locally."
}

PROCESSES=$(ps -aux | grep "[m]odelservice --master")

if [[ $PROCESSES != "" ]]; then
  echo "Killing with SIGINT: $PROCESSES"
  # Send SIGINT signal to worker process, shutting it down gracefully
  pkill -f "modelservice --master"
else
  echo "Did not find any Master processes to kill"
fi