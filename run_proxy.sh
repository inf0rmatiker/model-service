#!/bin/bash

function print_usage {
  echo -e "./run_proxy_server.sh <master_uri> <flask_port>"
  echo -e "EXAMPLE ./run_proxy_server.sh master:50051 5000"
}

if [[ $# -eq 2 ]]; then

  PROXY_PROCESSES=$(ps -aux | grep "[m]odelservice --proxy")
  [ "$PROXY_PROCESSES" != "" ] && echo -e "Found flaskserver processes running!\n$PROXY_PROCESSES\nPlease kill first before starting." && exit 1

  MASTER_URI=$1
  PROXY_PORT=$2
  ./bin/python3.8 -m modelservice --proxy --master_uri="$MASTER_URI" --port="$PROXY_PORT"

else
  print_usage
fi
