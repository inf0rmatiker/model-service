#!/bin/bash

function print_usage {
  echo -e "./kill_proxy.sh"
  echo -e "\tDESCRIPTION Shuts down the Proxy node locally."
}

PROCESSES=$(ps -aux | grep "[m]odelservice --proxy")

if [[ $PROCESSES != "" ]]; then
  echo "Killing with SIGINT: $PROCESSES"
  # Send SIGINT signal to worker process, shutting it down gracefully
  pkill -f "modelservice --proxy"
else
  echo "Did not find any Proxy processes to kill"
fi