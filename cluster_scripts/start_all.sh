#!/bin/bash

function print_usage {
  echo -e "./start_all.sh"
  echo -e "\tEXAMPLE Starts the Proxy, the Master, and all Workers remotely."
  echo -e "\tPlease make sure you have a 'workers' file, with the hostnames of each worker separated by newlines"
}

[[ ! -f "./env.sh" ]] && echo -e "No env.sh script found! Please create one using env.sh.example" && exit 1
source ./env.sh

CURR_DIR=$(pwd)
MODEL_SERVICE_DIR="$HOME/model-service"

cd "$MODEL_SERVICE_DIR" || exit 1
echo -e "Starting Master..."
nohup ./run_master.sh "$MASTER_PORT" > "master_$(hostname).log" & disown
sleep 5
echo -e "Starting Proxy..."
nohup ./run_proxy.sh "$(hostname):$MASTER_PORT" "$PROXY_PORT" > "proxy_$(hostname).log" & disown
sleep 1

cd "$CURR_DIR" || exit 1
echo -e "Starting Workers..."
./start_workers.sh "$(hostname):$MASTER_PORT" "$WORKERS_FILE"