#!/bin/bash
# Test the DOOM-COBOL system with mock components

echo "======================================"
echo "DOOM-COBOL Mock System Test"
echo "======================================"
echo
echo "This tests the system without needing modified DOOM"
echo

# Create logs directory
mkdir -p logs

# Cleanup function
cleanup() {
    echo
    echo "Cleaning up..."
    jobs -p | xargs -r kill 2>/dev/null || true
}
trap cleanup EXIT

# 1. Start mock state writer
echo "1. Starting mock state writer..."
python3 - << 'EOF' &
import time
import json

tick = 0
health = 100
x, y = 1000, 1000

print("Mock state writer started")
while True:
    tick += 1
    
    # Write COBOL format
    with open('/tmp/doom_state.dat', 'w') as f:
        f.write(f"STATE {tick:08d} 01\n")
        f.write(f"PLAYER{x:+08d}{y:+08d}+0000000+090{health:03d}050\n")
        f.write(f"AMMO  0050002001000040 2\n")
    
    # Write JSON format
    state = {
        "tick": tick,
        "health": health,
        "armor": 50,
        "ammo": [50, 20, 100, 40],
        "x": x, "y": y
    }
    with open('/tmp/doom_state.json', 'w') as f:
        json.dump(state, f)
    
    # Simulate movement
    x += 10
    if tick % 20 == 0:
        health = max(0, health - 5)
    
    time.sleep(0.1)
EOF
MOCK_PID=$!
echo "   ✓ Mock state writer started (PID: $MOCK_PID)"
sleep 1

# 2. Start mock network input receiver
echo "2. Starting mock input receiver..."
python3 - << 'EOF' > logs/mock_input.log 2>&1 &
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('localhost', 31338))
print("Mock input receiver on port 31338")

while True:
    data, addr = sock.recvfrom(1024)
    command = data.decode('ascii')
    print(f"Received command: {command} from {addr}")
EOF
INPUT_PID=$!
echo "   ✓ Mock input receiver started (PID: $INPUT_PID)"
sleep 1

# 3. Start the AI bridge
echo "3. Starting AI bridge..."
python3 bridge/file_state_bridge.py > logs/bridge.log 2>&1 &
BRIDGE_PID=$!
echo "   ✓ AI bridge started (PID: $BRIDGE_PID)"
sleep 1

# 4. Run test sequence
echo
echo "Running test sequence..."
echo "========================"

# Monitor for 10 seconds
for i in {1..10}; do
    echo
    echo "Cycle $i:"
    
    # Show current state
    if [ -f /tmp/doom_state.dat ]; then
        echo "State: $(head -1 /tmp/doom_state.dat)"
        
        # Extract health
        HEALTH=$(grep "^PLAYER" /tmp/doom_state.dat | sed 's/.*\([0-9]\{3\}\)[0-9]\{3\}$/\1/')
        echo "Health: $HEALTH"
    fi
    
    # Show commands sent
    if [ -f logs/mock_input.log ]; then
        echo "Last command: $(tail -1 logs/mock_input.log | grep "Received" | tail -1)"
    fi
    
    sleep 1
done

echo
echo "======================================"
echo "Mock Test Complete!"
echo "======================================"
echo
echo "Check logs:"
echo "- State updates: /tmp/doom_state.dat"
echo "- Commands received: logs/mock_input.log"
echo "- Bridge activity: logs/bridge.log"
echo

# Show summary
echo "Summary:"
grep -c "Received command" logs/mock_input.log 2>/dev/null && \
    echo "- Commands sent: $(grep -c "Received command" logs/mock_input.log)"
echo "- Final state: $(tail -1 /tmp/doom_state.dat)"

exit 0