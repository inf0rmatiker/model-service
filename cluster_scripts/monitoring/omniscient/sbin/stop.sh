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

    echo "stopping $HOST"
    if [ "$HOST" == "$(hostname)" ]; then
        # stop local monitors
        # (kill $(cat "$LOG_FILE.pid")) &
        kill $(ps -aux | grep '[n]mon' | awk '{print $2}')
    else
        # stop remote monitors
        (ssh "$HOST" -n -o ConnectTimeout=500 "kill \$(ps -aux | grep '[n]mon' | awk '{print \$2}')") &
    fi
done < "$HOST_FILE"

# wait for all to complete
wait

echo "[/] stopped monitor with id '$1'"