#!/bin/bash

function print_usage {
  echo -e "./start_omni.sh <name>"
  echo -e "EXAMPLE ./start_omni.sh my_test_benchmark"
}

[[ $# -eq 1 ]] || (print_usage; exit 1)

BENCHMARK_NAME=$1
echo "$BENCHMARK_NAME" > ".benchmark_name"

MON_ID=$(omni start | grep "started monitor with id" | awk '{ print $6 }' | sed -e "s/'//g")
echo "$MON_ID" > ".mon_id"