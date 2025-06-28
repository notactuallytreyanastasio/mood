#!/bin/bash
# Run DOOM and capture its output/stats

echo "Starting DOOM with statistics output..."
echo "======================================"
echo

# Create a named pipe for output
PIPE=/tmp/doom_output
mkfifo $PIPE 2>/dev/null || true

# Start chocolate-doom with debugging/stats
chocolate-doom \
    -iwad wads/doom1.wad \
    -window \
    -geometry 640x480 \
    -statdump /tmp/doom_stats.txt \
    2>&1 | tee $PIPE &

DOOM_PID=$!

# Monitor the output
echo "DOOM running (PID: $DOOM_PID)"
echo "Monitoring output..."
echo

# Read from pipe
while read line; do
    echo "DOOM: $line"
    
    # Look for game state info in output
    if [[ "$line" == *"player"* ]] || [[ "$line" == *"health"* ]]; then
        echo ">>> STATE: $line"
    fi
done < $PIPE &

# Also monitor any stat dumps
while true; do
    if [ -f /tmp/doom_stats.txt ]; then
        echo "=== STATS DUMP ==="
        cat /tmp/doom_stats.txt
        echo "=================="
    fi
    sleep 1
done &

wait $DOOM_PID
echo "DOOM exited"