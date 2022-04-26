#!/bin/bash

# create log directories on each HOST
while read -r LINE; do
    # parse host and log directory
    HOST=$(echo "$LINE" | awk '{print $1}')
    DIRECTORY=$(echo "$LINE" | awk '{print $2}')

    if [ "$HOST" == "$(hostname)" ]; then
        mkdir -p "$DIRECTORY"
        chmod 644 "$DIRECTORY"
    else
        ssh -n "$HOST" "mkdir -p $DIRECTORY && chmod 644 $DIRECTORY"
    fi
    echo "Finished initializing nmon dir $DIRECTORY on $HOST"
done < "$HOST_FILE"