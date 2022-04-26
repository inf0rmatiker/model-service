#!/bin/bash

# check arguments
if [ $# != 1 ]; then
    echo "$USAGE"
    exit 1
fi

# iterate over hosts
while read -r LINE; do
    # parse host and log directory
    HOST=$(echo "$LINE" | awk '{print $1}')
    DIRECTORY=$(echo "$LINE" | awk '{print $2}')

    LOG_FILE="$DIRECTORY/${HOST}_$1"

    if [ "$HOST" == "$(hostname)" ]; then
        # remove local monitors
        (rm "$LOG_FILE"*) &
    else
        # remove remote monitors
        (ssh "$HOST" -n -o ConnectTimeout=500 "rm $LOG_FILE*") &
    fi
done < "$HOST_FILE"

# wait for all to complete
wait

echo "[-] removed monitor with id '$1'"