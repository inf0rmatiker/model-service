#!/bin/bash

function print_usage {
  echo -e "./run_worker.sh <master_uri> <worker_port> <data_dir> [--daemon]"
  echo -e "EXAMPLE ./run_worker.sh master:50051 5000 /tmp/model_service --daemon"
}

if [[ $# -ge 3 ]]; then

  WORKER_PROCESSES=$(ps -aux | grep "[m]odelservice --worker")
  [ "$WORKER_PROCESSES" != "" ] && echo -e "Found worker processes running!\n$WORKER_PROCESSES\nPlease kill first before starting." && exit 1

  MASTER_URI=$1
  WORKER_PORT=$2
  DATA_DIR=$3
  DAEMON=$4

  if [ "$DAEMON" == "--daemon" ]; then
    nohup ./bin/python3.8 -m modelservice --worker --master_uri="$MASTER_URI" --port="$WORKER_PORT"  --data_dir="$DATA_DIR" > "worker_log_$(hostname).log" 2>&1 & disown
  else
    ./bin/python3.8 -m modelservice --worker --master_uri="$MASTER_URI" --port="$WORKER_PORT" --data_dir="$DATA_DIR"
  fi

else
  print_usage
fi
