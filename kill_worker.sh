#!/bin/bash

function print_usage {
  echo -e "./kill_worker.sh"
  echo -e "\tDESCRIPTION Shuts down the Worker node locally."
}

PROCESSES=$(ps -aux | grep "[m]odelservice --worker")

if [[ $PROCESSES != "" ]]; then
  echo "Killing with SIGINT: $PROCESSES"
  # Send SIGINT signal to worker process, shutting it down gracefully
  pkill -f "modelservice --worker"
else
  echo "Did not find any Workerr processes to kill"
fi