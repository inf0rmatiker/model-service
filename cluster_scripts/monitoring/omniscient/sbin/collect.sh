#!/bin/bash

# check arguments
if [ $# != 2 ]; then
    echo "$USAGE"
    exit 1
fi

# if doesn't exist -> create destination directory
if [ ! -d "$2" ]; then
    mkdir -p "$2"
fi

# iterate over hosts
while read -r LINE; do
    # parse host and log directory
    HOST=$(echo "$LINE" | awk '{print $1}')
    DIRECTORY=$(echo "$LINE" | awk '{print $2}')

    LOG_FILE="$DIRECTORY/${HOST}_$1"

    if [ "$HOST" == "$(hostname)" ]; then
        # convert local nmon to csv
        ([ ! -f "$LOG_FILE.nmon.csv" ] && \
            python3 "$SCRIPT_DIR/nmon2csv.py" "$LOG_FILE.nmon" --metrics="$NMON_METRICS" > "$LOG_FILE.nmon.csv") &
    else
        # convert remote nmon to csv
        (ssh "$HOST" -n -o ConnectTimeout=500 \
            "[ ! -f \"$LOG_FILE.nmon.csv\" ] && \
                python3 $SCRIPT_DIR/nmon2csv.py $LOG_FILE.nmon --metrics=\"$NMON_METRICS\" \
                    > $LOG_FILE.nmon.csv") &
    fi
done < "$HOST_FILE"

# wait for all to complete
wait

echo "[+] compiled nmon csv files"

# iterate over hosts
NODE_ID=0
while read -r LINE; do
    # parse host and log directory
    HOST=$(echo "$LINE" | awk '{print $1}')
    DIRECTORY=$(echo "$LINE" | awk '{print $2}')

    LOG_FILE="$DIRECTORY/${HOST}_$1"

    if [ "$HOST" == "$(hostname)" ]; then
        # copy local data to collect directory
        cp "$LOG_FILE.nmon.csv" "$2/$NODE_ID-$HOST.nmon.csv"
    else
        # copy remote data to collect directory
        scp "$HOST:$LOG_FILE.nmon.csv" "$2/$NODE_ID-$HOST.nmon.csv"
    fi

    NODE_ID=$(( NODE_ID + 1 ))
done < "$HOST_FILE"

echo "[+] downloaded host monitor files"

# combine host monitor files
python3 "$SCRIPT_DIR/csv-merge.py" "$2"/*nmon.csv > "$2/aggregate.nmon.csv"

echo "[+] combined host monitor files"