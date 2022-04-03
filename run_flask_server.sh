#!/bin/bash

function print_usage {
  echo -e "./run_flask_server.sh <master_uri> <flask_port>"
  echo -e "EXAMPLE ./run_flask_server.sh master:50051 5000"
}

if [[ $# -eq 2 ]]; then

  FLASK_PROCESSES=$(ps -aux | grep "[p]roxy --flaskserver")
  [ "$FLASK_PROCESSES" != "" ] && echo -e "Found flaskserver processes running!\n$FLASK_PROCESSES\nPlease kill first before starting." && exit 1

  MASTER_URI=$1
  FLASK_PORT=$2
  python3 -m proxy --flaskserver --master_uri="$MASTER_URI" --port="$FLASK_PORT"

else
  print_usage
fi
