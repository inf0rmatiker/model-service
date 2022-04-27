#!/bin/bash

# check arguments
if [ $# != 0 ]; then
    echo "$USAGE"
    exit 1
fi

# iterate over hosts
while read -r LINE; do
    # parse host and log directory
    HOST=$(echo "$LINE" | awk '{print $1}')
    DIRECTORY=$(echo "$LINE" | awk '{print $2}')

    echo "$HOST: Cleaning up directory $DIRECTORY"

    if [ "$HOST" == "$(hostname)" ]; then
        # clean up local monitors
        rm "$DIRECTORY"/*
    else
        # clean up remote monitors
        ssh "$HOST" -n -o ConnectTimeout=500 "rm $DIRECTORY/*"
    fi
done < "$HOST_FILE"