#!/bin/bash
# Start the complete DOOM-COBOL system

set -e

echo "======================================"
echo "DOOM-COBOL Full System Startup"
echo "======================================"

# Check if modified DOOM is built
if [ ! -f "linuxdoom-1.10/linux/linuxxdoom" ]; then
    echo "Modified DOOM not found. Building..."
    ./scripts/build_modified_doom.sh || exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo
    echo "Shutting down..."
    
    # Kill all background processes
    jobs -p | xargs -r kill 2>/dev/null || true
    
    # Clean up temp files
    rm -f /tmp/doom_state.dat
    
    echo "Cleanup complete"
}

trap cleanup EXIT

# Start components
echo
echo "Starting system components..."
echo

# 1. Start modified DOOM
echo "1. Starting DOOM with state export..."
cd linuxdoom-1.10/linux
./linuxxdoom -iwad ../../wads/doom1.wad &
DOOM_PID=$!
cd ../..
echo "   ✓ DOOM started (PID: $DOOM_PID)"
sleep 3

# 2. Start state receiver bridge
echo "2. Starting state receiver bridge..."
python3 bridge/state_receiver.py > logs/state_receiver.log 2>&1 &
BRIDGE_PID=$!
echo "   ✓ State receiver started (PID: $BRIDGE_PID)"
sleep 1

# 3. Start network controller interface
echo "3. Starting network controller..."
python3 bridge/doom_network_controller.py server > logs/controller.log 2>&1 &
CONTROLLER_PID=$!
echo "   ✓ Network controller started (PID: $CONTROLLER_PID)"
sleep 1

# 4. Optional: Start web dashboard
if [ "$1" != "--no-web" ]; then
    echo "4. Starting web dashboard..."
    cd web-ui
    python3 -m http.server 8080 > ../logs/web.log 2>&1 &
    WEB_PID=$!
    cd ..
    echo "   ✓ Web dashboard at http://localhost:8080"
fi

echo
echo "======================================"
echo "System Running!"
echo "======================================"
echo
echo "Components:"
echo "- DOOM: Modified Linux DOOM with state export"
echo "- State: UDP port 31337 → Python bridge"
echo "- Input: UDP port 31338 ← Network commands"
echo "- COBOL: /tmp/doom_state.dat (COBOL format)"
echo
echo "Logs:"
echo "- State receiver: logs/state_receiver.log"
echo "- Controller: logs/controller.log"
echo
echo "Commands:"
echo "- Send command: echo 'FORWARD 2' | nc -u localhost 31338"
echo "- View state: tail -f /tmp/doom_state.dat"
echo
echo "Press Ctrl+C to shutdown"
echo

# Keep running
while true; do
    # Check if DOOM is still running
    if ! kill -0 $DOOM_PID 2>/dev/null; then
        echo "DOOM process terminated"
        break
    fi
    
    # Show periodic status
    if [ -f /tmp/doom_state.dat ]; then
        echo -n "Latest state: "
        head -1 /tmp/doom_state.dat
    fi
    
    sleep 5
done