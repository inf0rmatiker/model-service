#!/bin/bash

function print_usage {
  echo -e "./kill_all.sh"
  echo -e "\tDESCRIPTION Remotely shuts down all Workers, the Master, then finally the Flask server."
  echo -e "\tPlease make sure you have a 'workers' file, with the hostnames of each worker separated by newlines"
}

[[ ! $# -eq 0 ]] && print_usage && exit 1

echo "Killing Workers..." && ./kill_workers.sh
echo "Killing Master..." && ../kill_master.sh
echo "Killing Proxy..." && ../kill_proxy.sh