#!/bin/bash
# Test state capture without needing DOOM

echo "Testing State Capture System"
echo "============================"

# Test 1: SQLite module
echo
echo "1. Testing SQLite..."
python3 -c "
import sqlite3
import struct
print('✓ SQLite available')
print('✓ struct module available')
" || {
    echo "✗ Missing Python modules"
    exit 1
}

# Test 2: Create test state
echo
echo "2. Creating test state file..."
cat > /tmp/doom_state.dat << EOF
STATE 00001234 01
PLAYER+0001024+0001024+0000000+090075050
AMMO  0050002001000040 2
ENEMY 09 100 +0001200 +0001100 00256
EOF
echo "✓ Created /tmp/doom_state.dat"

# Test 3: Test SQLite capture
echo
echo "3. Testing SQLite capture (5 seconds)..."
python3 build_system/doom_state_sqlite.py > test_sqlite.log 2>&1 &
SQLITE_PID=$!

sleep 2

# Send test UDP packet
echo "4. Sending test UDP packet..."
python3 -c "
import socket
import struct

# Create test packet
magic = 0x4D4F4F44  # 'DOOM'
version = 1
tick = 1234

# Pack header
data = struct.pack('<III', magic, version, tick)

# Pack player state
data += struct.pack('<18i',
    75,  # health
    50,  # armor
    50, 20, 100, 40,  # ammo
    2,   # weapon
    1024 << 16,  # x (fixed point)
    1024 << 16,  # y
    0,   # z
    0x40000000,  # angle (90 degrees)
    0, 0,  # momentum
    1,   # level
    5,   # kills
    10,  # items
    2,   # secrets
    1    # enemy_count
)

# Add one enemy
data += struct.pack('<5i',
    9,    # type
    100,  # health
    1200 << 16,  # x
    1100 << 16,  # y
    256 << 16    # distance
)

# Send packet
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(data, ('localhost', 31337))
sock.close()

print('✓ Sent test packet')
"

sleep 3

# Kill SQLite capture
kill $SQLITE_PID 2>/dev/null

# Test 4: Check database
echo
echo "5. Checking database..."
if [ -f "doom_state.db" ]; then
    echo "✓ Database created"
    
    # Query it
    COUNT=$(sqlite3 doom_state.db "SELECT COUNT(*) FROM game_state;" 2>/dev/null || echo "0")
    echo "  States captured: $COUNT"
    
    if [ "$COUNT" -gt 0 ]; then
        echo
        echo "Sample data:"
        sqlite3 -header -column doom_state.db \
            "SELECT tick, health, armor, x>>16 as x, y>>16 as y 
             FROM game_state LIMIT 5;"
        
        echo
        echo "COBOL format:"
        sqlite3 doom_state.db \
            "SELECT record_data FROM cobol_state LIMIT 5;"
    fi
else
    echo "✗ Database not created"
fi

echo
echo "============================"
echo "Test complete!"
echo
echo "If everything worked, you can now run:"
echo "  ./master_control.sh"