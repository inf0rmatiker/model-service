#!/bin/bash

function print_usage {
  echo -e "./kill_workers.sh"
  echo -e "\tDESCRIPTION Remotely shuts down workers, using the './workers' file."
  echo -e "\tPlease make sure you have a 'workers' file, with the hostnames of each worker separated by newlines"
}

if [[ $# -eq 0 ]]; then
  WORKER_HOSTS_FILE="./workers"
  for WORKER_HOST in $(cat "$WORKER_HOSTS_FILE"); do
    echo -e "Killing worker on $WORKER_HOST:50055"
    ssh "$WORKER_HOST" "cd ~/model-service && ./kill_worker.sh"
  done
else
  print_usage
fi