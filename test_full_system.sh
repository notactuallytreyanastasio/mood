#!/bin/bash
# Full DOOM-COBOL System Test
# This script starts everything and runs a test sequence

set -e

echo "=== DOOM-COBOL Full System Test ==="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running!"
    exit 1
fi

# Step 1: Start Docker services
echo "1. Starting Docker services..."
make -f Makefile.simple up-simple

# Wait for services to be ready
echo "   Waiting for services to start..."
sleep 5

# Test COBOL interface
echo "   Testing COBOL interface..."
if echo "STATUS" | nc localhost 9999 | grep -q "OK"; then
    echo "   ✓ COBOL interface is running"
else
    echo "   ✗ COBOL interface failed to start"
    exit 1
fi

# Step 2: Start DOOM
echo ""
echo "2. Starting DOOM..."
echo "   NOTE: If DOOM doesn't start, you may need to:"
echo "   - Install chocolate-doom: brew install chocolate-doom"
echo "   - Download doom1.wad from shareware DOOM"
echo ""

# Check if we can find DOOM
if command -v chocolate-doom &> /dev/null; then
    echo "   Found chocolate-doom"
elif command -v gzdoom &> /dev/null; then
    echo "   Found gzdoom"
else
    echo "   WARNING: No DOOM executable found!"
    echo "   Install with: brew install chocolate-doom"
fi

# Start DOOM in background
./doom-launcher/launch_doom.sh --no-iwad &
LAUNCHER_PID=$!

# Wait for DOOM to start
echo "   Waiting for DOOM to initialize..."
sleep 5

# Step 3: Start the host bridge
echo ""
echo "3. Starting host bridge..."
cd bridge
python3 bridge_runner.py &
BRIDGE_PID=$!
cd ..

# Wait for bridge to initialize
sleep 2

# Step 4: Run test sequence
echo ""
echo "4. Running DOOM-COBOL test sequence..."
echo ""
echo "   This will demonstrate COBOL controlling DOOM:"
echo ""

# Function to send command and wait
send_command() {
    local cmd="$1"
    local wait="$2"
    echo "   → Sending: $cmd"
    echo "$cmd" | nc localhost 9999
    echo "$cmd" > /tmp/doom-cobol-commands.txt
    sleep "$wait"
}

# Test sequence
echo "   === Starting DOOM Control Demo ==="
echo ""

send_command "MOVE FORWARD 2" 3
send_command "TURN RIGHT 45" 1
send_command "MOVE FORWARD 1" 2
send_command "TURN RIGHT 45" 1
send_command "SHOOT 3" 2
send_command "TURN LEFT 90" 1
send_command "MOVE FORWARD 2" 3
send_command "USE" 1
send_command "MOVE BACK 1" 2

echo ""
echo "   === Demo Complete ==="
echo ""

# Step 5: Check system status
echo "5. System Status:"
echo ""
echo "   Checking web UI..."
curl -s http://localhost:8080/api/status | jq '.' || echo "   Web UI not responding"

echo ""
echo "   COBOL Interface logs:"
docker logs doom-cobol-interface --tail 10

echo ""
echo "=== Test Complete ==="
echo ""
echo "The system is now running:"
echo "  - COBOL Interface: localhost:9999"
echo "  - Web Dashboard: http://localhost:8080"
echo "  - DOOM: Running (check your display)"
echo ""
echo "You can continue sending commands:"
echo "  echo 'MOVE FORWARD' | nc localhost 9999"
echo "  echo 'TURN RIGHT 90' | nc localhost 9999"
echo "  echo 'SHOOT' | nc localhost 9999"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user to stop
trap cleanup INT

cleanup() {
    echo ""
    echo "Stopping services..."
    kill $BRIDGE_PID 2>/dev/null || true
    kill $LAUNCHER_PID 2>/dev/null || true
    if [ -f /tmp/doom-cobol.pid ]; then
        kill $(cat /tmp/doom-cobol.pid) 2>/dev/null || true
        rm /tmp/doom-cobol.pid
    fi
    make -f Makefile.simple down-simple
    echo "All services stopped."
    exit 0
}

# Keep running
while true; do
    sleep 1
done