#!/bin/bash

BENCHMARK_NAME=$1
export BENCHMARK_NAME

[[ -f ".benchmark_name" ]] || (echo "Benchmark name not set!" ; exit 1)
[[ -f ".mon_id" ]] || (echo "MON_ID not set!" ; exit 1)

BENCHMARK_NAME=$(cat ".benchmark_name")
MON_ID=$(cat ".mon_id")

echo -e "Stopping benchmark $BENCHMARK_NAME with monitor id $MON_ID..."
omni stop "$MON_ID"

echo -e "Collecting..."
omni collect "$MON_ID" "./$BENCHMARK_NAME"
