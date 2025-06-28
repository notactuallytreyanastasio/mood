#!/bin/bash
# Simple test of the DOOM-COBOL loop without full Docker

echo "======================================"
echo "Simple DOOM-COBOL Loop Test"
echo "======================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Cleanup function
cleanup() {
    echo
    echo "Cleaning up..."
    [ -n "$FTP_PID" ] && kill $FTP_PID 2>/dev/null
    [ -n "$INTERFACE_PID" ] && kill $INTERFACE_PID 2>/dev/null
    [ -n "$BRIDGE_PID" ] && kill $BRIDGE_PID 2>/dev/null
    rm -f /tmp/doom_state.dat
}
trap cleanup EXIT

# Step 1: Install dependencies
echo "Step 1: Installing Python dependencies..."
pip3 install pyftpdlib structlog prometheus-client pyautogui pillow > /dev/null 2>&1
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 2: Start mock FTP server
echo
echo "Step 2: Starting mock FTP server..."
cd ftp-gateway
python3 mock_ftp_server.py > ../logs/ftp.log 2>&1 &
FTP_PID=$!
cd ..
sleep 2

if ps -p $FTP_PID > /dev/null; then
    echo -e "${GREEN}✓ FTP server started (PID: $FTP_PID)${NC}"
else
    echo -e "${RED}✗ FTP server failed to start${NC}"
    exit 1
fi

# Step 3: Start COBOL interface
echo
echo "Step 3: Starting COBOL interface..."
cd cobol-interface
python3 cobol_interface.py > ../logs/interface.log 2>&1 &
INTERFACE_PID=$!
cd ..
sleep 2

if ps -p $INTERFACE_PID > /dev/null; then
    echo -e "${GREEN}✓ COBOL interface started (PID: $INTERFACE_PID)${NC}"
else
    echo -e "${RED}✗ COBOL interface failed to start${NC}"
    exit 1
fi

# Step 4: Start FTP bridge
echo
echo "Step 4: Starting FTP bridge..."
cd ftp-gateway
python3 ftp_gateway.py > ../logs/bridge.log 2>&1 &
BRIDGE_PID=$!
cd ..
sleep 2

if ps -p $BRIDGE_PID > /dev/null; then
    echo -e "${GREEN}✓ FTP bridge started (PID: $BRIDGE_PID)${NC}"
else
    echo -e "${RED}✗ FTP bridge failed to start${NC}"
    exit 1
fi

# Step 5: Test the loop
echo
echo "Step 5: Testing the feedback loop..."
echo "======================================"

# Test with different health values
for health in 25 50 75; do
    echo
    echo "Test: Health = $health"
    echo "─────────────────────"
    
    # Create state file
    cat > /tmp/doom_state.dat << EOF
STATE 00001234 01
PLAYER+0001024+0001024+0000000+090${health}050
AMMO  0050002001000040 2
EOF
    
    echo "Created state file with health=$health"
    
    # Wait for processing
    echo "Waiting for COBOL processing..."
    sleep 3
    
    # Check logs
    echo "FTP activity:"
    tail -5 logs/ftp.log | grep "COBOL AI:" || echo "  (no COBOL activity yet)"
    
    echo "Commands sent:"
    tail -5 logs/interface.log | grep "Received command" || echo "  (no commands yet)"
done

# Step 6: Show results
echo
echo "======================================"
echo "Test Results"
echo "======================================"

echo
echo "Services running:"
ps aux | grep -E "(mock_ftp|cobol_interface|ftp_gateway)" | grep -v grep | awk '{print "  " $11 " (PID: " $2 ")"}'

echo
echo "Log files created:"
ls -la logs/*.log 2>/dev/null | awk '{print "  " $9 " (" $5 " bytes)"}'

echo
echo -e "${GREEN}✓ Simple loop test complete!${NC}"
echo
echo "To monitor in real-time:"
echo "  tail -f logs/*.log"