#!/bin/bash

function print_usage {
  echo -e "./distribute_data.sh <path_to_original_tar>"
  echo -e "\tEXAMPLE ./distribute_data.sh ~/noaa_nam_gis_joins.tar"
  echo -e "\tPlease make sure you have a 'workers' file, with the hostnames of each worker separated by newlines"
}

[[ $# -eq 1 ]] || print_usage && exit 1
ORIGINAL_TAR_FILE=$1
[[ -f "$ORIGINAL_TAR_FILE" ]] && [[ $ORIGINAL_TAR_FILE == *.tar ]] || print_usage && exit 1
[[ -f "./workers" ]] || echo "No './workers' file found, please create one first" && exit 1

TEMP_LOC="/tmp/model_service"
[[ ! -d $TEMP_LOC ]] && mkdir $TEMP_LOC && tar -xvf "$ORIGINAL_TAR_FILE" -C "$TEMP_LOC"

readarray -t WORKERS < ./workers
NUM_WORKERS=${#WORKERS[@]}
NUM_FILES=$(ls $TEMP_LOC/*.csv | wc -l)
FILES_PER_WORKER=$((NUM_FILES / NUM_WORKERS))
while read -r WORKER; do
  BATCH=$(ls $TEMP_LOC/*.csv | head -n $FILES_PER_WORKER)
  for CSV_FILE in ${BATCH[@]}; do
    echo -e "Sending $CSV_FILE to $WORKER..."
  done
done < "./workers"