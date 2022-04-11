#!/bin/bash

function print_usage {
  echo -e "./run_master.sh <master_port>"
  echo -e "EXAMPLE ./run_master.sh 50051"
}

if [[ $# -eq 1 ]]; then

  MASTER_PROCESSES=$(ps -aux | grep "[m]odelservice --master")
  [ "$MASTER_PROCESSES" != "" ] && echo -e "Found master processes running!\n$MASTER_PROCESSES\nPlease kill first before starting." && exit 1

  MASTER_PORT=$1
  python3.8 -m modelservice --master --port="$MASTER_PORT"

else
  print_usage
fi
