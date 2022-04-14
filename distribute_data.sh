#!/bin/bash

function print_usage {
  echo -e "./distribute_data.sh <path_to_original_tar>"
  echo -e "\tEXAMPLE ./distribute_data.sh ~/noaa_nam_gis_joins.tar"
  echo -e "\tPlease make sure you have a 'workers' file, with the hostnames of each worker separated by newlines"
}

[[ ! $# -eq 1 ]] && print_usage && exit 1

ORIGINAL_TAR_FILE=$1
if [[ ! -f "$ORIGINAL_TAR_FILE" || ! $ORIGINAL_TAR_FILE == *.tar ]]; then
  print_usage ; exit 1
fi

[[ ! -f "./workers" ]] && echo "No './workers' file found, please create one first" && exit 1

TEMP_LOC="/tmp/model_service"
[[ ! -d $TEMP_LOC ]] && mkdir $TEMP_LOC && tar -xvf "$ORIGINAL_TAR_FILE" -C "$TEMP_LOC"

readarray -t WORKERS < ./workers
NUM_WORKERS=${#WORKERS[@]}
NUM_FILES=$(ls $TEMP_LOC/*.csv | wc -l)
FILES_PER_WORKER=$((NUM_FILES / NUM_WORKERS))
while read -r WORKER; do
  BATCH=$(ls $TEMP_LOC/*.csv | head -n $FILES_PER_WORKER)
  ssh -n "$WORKER" "mkdir /tmp/model_service"
  for CSV_FILE in ${BATCH[@]}; do
    echo -e "Sending $CSV_FILE to $WORKER..."
    scp "$CSV_FILE" "$WORKER:/tmp/model_service/"
    rm "$CSV_FILE"
  done
done < "./workers"

# Finish up with just the last worker
scp $TEMP_LOC/*.csv "$WORKER:/tmp/model_service/"

echo -e "Finished distributing $NUM_FILES / $NUM_WORKERS = ~$FILES_PER_WORKER files per worker"