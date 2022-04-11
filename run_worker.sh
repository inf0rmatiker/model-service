#!/bin/bash

function print_usage {
  echo -e "./run_worker.sh <master_uri> <worker_port>"
  echo -e "EXAMPLE ./run_worker.sh master:50051 5000"
}

if [[ $# -eq 2 ]]; then

  WORKER_PROCESSES=$(ps -aux | grep "[m]odelservice --worker")
  [ "$WORKER_PROCESSES" != "" ] && echo -e "Found worker processes running!\n$WORKER_PROCESSES\nPlease kill first before starting." && exit 1

  MASTER_URI=$1
  WORKER_PORT=$2
  python3.8 -m modelservice --worker --master_uri="$MASTER_URI" --port="$WORKER_PORT"

else
  print_usage
fi
