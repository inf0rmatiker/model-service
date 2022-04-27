#!/bin/bash

# check arguments
if [ $# != 0 ]; then
    echo "$USAGE"
    exit 1
fi

# ensure commands are installed
[ -z "$NMON_CMD" ] && echo "nmon command not found" && exit 1

MON_ID="$USER-$(date +%Y%m%d-%H%M%S)"

# iterate over hosts
while read -r LINE; do
    # parse host and log directory
    HOST=$(echo "$LINE" | awk '{print $1}')
    DIRECTORY=$(echo "$LINE" | awk '{print $2}')

    LOG_FILE="$DIRECTORY/${HOST}_${MON_ID}"
    echo "$HOST: Creating log file $LOG_FILE.nmon and pidfile $LOG_FILE.pid"

    if [ "$HOST" == "$(hostname)" ]; then
        # start local monitors
        ("$NMON_CMD" -F "$LOG_FILE.nmon" -c "$NMON_SNAPSHOTS" -s "$SNAPSHOT_SECONDS" -p >> "$LOG_FILE.pid") &
    else
        # start remote monitors
        (ssh "$HOST" -n -o ConnectTimeout=500 "$NMON_CMD -F $LOG_FILE.nmon -c $NMON_SNAPSHOTS -s $SNAPSHOT_SECONDS -p >> $LOG_FILE.pid") &
    fi
done < "$HOST_FILE"

# wait for all to complete
wait

echo "[+] started monitor with id '$MON_ID'"