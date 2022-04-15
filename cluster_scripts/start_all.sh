#!/bin/bash

function print_usage {
  echo -e "./start_all.sh"
  echo -e "\tEXAMPLE Starts the Proxy, the Master, and all Workers remotely."
  echo -e "\tPlease make sure you have a 'workers' file, with the hostnames of each worker separated by newlines"
}

CURR_DIR=$(pwd)
VALIDATION_SERVICE_DIR="$HOME/model-service"

cd "$VALIDATION_SERVICE_DIR" || exit 1
echo -e "Starting Master..."
nohup "./run_master.sh" 50051 > "master_$(hostname).log" & disown
sleep 5
echo -e "Starting Proxy..."
nohup "./run_proxy.sh" "$(hostname):50051" 5000 > "flask_server_$(hostname).log" & disown
sleep 1

cd "$CURR_DIR" || exit 1
echo -e "Starting Workers..."
./start_workers.sh "$(hostname):50051" "$WORKERS_FILE"