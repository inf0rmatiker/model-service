#!/bin/bash

# validate arguments
if [ $# != 2 ]; then
    exit 1
fi

OUTPUT="$1"

# initialize instance variables
STRIPPED="${2%.*}"
MON_ID=$(basename "$STRIPPED")

OUTPUT="$OUTPUT : $MON_ID"

# check if processes are running
while read -r PID; do
    if ps -p "$PID" > /dev/null; then
        STATUS="running"
    else
        STATUS="stopped"
    fi

    OUTPUT="$OUTPUT : $STATUS"
done < "$2"

# retrieve file sizes
NMON_SIZE=$(stat -c%s "$STRIPPED.nmon")

OUTPUT="$OUTPUT : $NMON_SIZE"

# print data to stdout
echo "$OUTPUT"