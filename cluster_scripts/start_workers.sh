#!/bin/bash

function print_usage {
  echo -e "./start_workers.sh"
  echo -e "\tDESCRIPTION Starts all Workers remotely. Must run this script from the Master node."
  echo -e "\tPlease make sure you have a 'workers' file, with the hostnames of each worker separated by newlines"
}

if [[ $# -eq 0 ]]; then

  [[ ! -f "./env.sh" ]] && echo -e "No env.sh script found! Please create one using env.sh.example" && exit 1
  source ./env.sh
  MASTER_HOSTNAME=$(hostname)
  MASTER_URI="$MASTER_HOSTNAME:$MASTER_PORT"
  DATA_DIR="/tmp/model_service"

  for WORKER_HOST in $(cat "$WORKER_HOSTS_FILE"); do
    echo -e "Launching worker on $WORKER_HOST:$WORKER_PORT"
    ssh "$WORKER_HOST" "cd ~/model-service && ./run_worker.sh $MASTER_URI $WORKER_PORT $DATA_DIR --daemon"
    sleep 1
  done
else
  print_usage
fi