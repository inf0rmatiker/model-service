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

    if [ "$HOST" == "$(hostname)" ]; then
        # list local monitors
        (find "$DIRECTORY" -name "*pid" -exec bash "$SCRIPT_DIR/format.sh" "$HOST" {} \;) &
    else
        # list remote monitors
        (ssh "$HOST" -n -o ConnectTimeout=500 "find $DIRECTORY -name \"*pid\" -exec bash $SCRIPT_DIR/format.sh '$HOST' {} \;") &
    fi
done < "$HOST_FILE"

# wait for all to complete
wait