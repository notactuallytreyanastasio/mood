#!/bin/bash
# Test the complete COBOL flow (Steps 1-8)

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Directories
WORK_DIR="$(pwd)"
MVS_DIR="$WORK_DIR/mvs_datasets"

echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        Testing DOOM-COBOL Flow (Steps 1-8)          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo

# Create directories
mkdir -p "$MVS_DIR" logs

# Step 1: Create test game state
echo -e "${BLUE}Step 1: Creating test game state...${NC}"
cat > "$MVS_DIR/DOOM.GAMESTAT" << 'EOF'
STATE   00001234012025010100000000000000000000000000000000000000000000000000000
PLAYER  +0001024+0001024+0000000+090025050A        0000000000000000000000000000
AMMO    0050002001000040200000000000000000000000000000000000000000000000000000
ENEMY   09100+0001200+0001100002560000        000000000000000000000000000000000
ENEMY   02075+0000800+0000900001280000        000000000000000000000000000000000
EOF

# Also create ASCII version
cat > "$MVS_DIR/DOOM.GAMESTAT.ASCII" << 'EOF'
STATE   00001234012025010100000000000000000000000000000000000000000000000000000
PLAYER  +0001024+0001024+0000000+090025050A        0000000000000000000000000000
AMMO    0050002001000040200000000000000000000000000000000000000000000000000000
ENEMY   09100+0001200+0001100002560000        000000000000000000000000000000000
ENEMY   02075+0000800+0000900001280000        000000000000000000000000000000000
EOF

echo -e "${GREEN}✓ Test game state created${NC}"

# Step 2: Simulate COBOL AI output
echo
echo -e "${BLUE}Step 2: Simulating COBOL AI output...${NC}"
cat > "$MVS_DIR/DOOM.COMMANDS.ASCII" << 'EOF'
COMMAND MOVE    BACK    00209SURVIVAL RETREAT                               
COMMAND TURN    LEFT    00453SECONDARY ACTION                               
COMMAND SHOOT           00015COMBAT ENGAGEMENT                              
COMMAND MOVE    FORWARD 00107EXPLORATION MODE                               
EOF

echo -e "${GREEN}✓ COBOL commands created${NC}"

# Step 3: Start FTP Gateway
echo
echo -e "${BLUE}Step 3: Starting MVS FTP Gateway...${NC}"
python3 ftp-gateway/mvs_ftp_gateway.py > logs/ftp_gateway.log 2>&1 &
FTP_PID=$!
sleep 2

if ps -p $FTP_PID > /dev/null; then
    echo -e "${GREEN}✓ FTP Gateway running (PID: $FTP_PID)${NC}"
else
    echo -e "${RED}✗ FTP Gateway failed to start${NC}"
    exit 1
fi

# Step 4: Start Web Server
echo
echo -e "${BLUE}Step 4: Starting COBOL Action Web Server...${NC}"
python3 web-ui/cobol_action_server.py --test > logs/web_server.log 2>&1 &
WEB_PID=$!
sleep 3

if ps -p $WEB_PID > /dev/null; then
    echo -e "${GREEN}✓ Web Server running (PID: $WEB_PID)${NC}"
else
    echo -e "${RED}✗ Web Server failed to start${NC}"
    kill $FTP_PID 2>/dev/null
    exit 1
fi

# Step 5: Test API endpoints
echo
echo -e "${BLUE}Step 5: Testing API endpoints...${NC}"

# Test status
echo -n "Testing /api/status... "
STATUS=$(curl -s http://localhost:8080/api/status | python3 -c "import json, sys; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "failed")
if [ "$STATUS" = "online" ]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Test latest action
echo -n "Testing /api/actions/latest... "
LATEST=$(curl -s http://localhost:8080/api/actions/latest | python3 -c "import json, sys; d=json.load(sys.stdin); print(d.get('action', {}).get('command', 'none'))" 2>/dev/null || echo "failed")
if [ "$LATEST" != "none" ] && [ "$LATEST" != "failed" ]; then
    echo -e "${GREEN}✓ Latest: $LATEST${NC}"
else
    echo -e "${YELLOW}! No actions yet${NC}"
fi

# Step 6: Trigger new commands
echo
echo -e "${BLUE}Step 6: Adding new commands...${NC}"
cat >> "$MVS_DIR/DOOM.COMMANDS.ASCII" << 'EOF'
COMMAND WAIT            00207NO ACTION DETERMINED                           
COMMAND USE             00001DOOR DETECTED                                  
EOF
echo -e "${GREEN}✓ Added 2 new commands${NC}"

# Wait for processing
sleep 2

# Step 7: Check results
echo
echo -e "${BLUE}Step 7: Checking processed commands...${NC}"
echo
echo "Recent actions:"
curl -s http://localhost:8080/api/actions/recent | python3 -m json.tool 2>/dev/null | head -20 || echo "Failed to get actions"

# Step 8: Display summary
echo
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo
echo "Services Running:"
echo "  - FTP Gateway: http://localhost:2121"
echo "  - Web Server: http://localhost:8080"
echo
echo "Files Created:"
echo "  - $MVS_DIR/DOOM.GAMESTAT (game state)"
echo "  - $MVS_DIR/DOOM.COMMANDS.ASCII (commands)"
echo
echo "Next Steps:"
echo "  1. Open http://localhost:8080 in browser"
echo "  2. Watch commands appear in real-time"
echo "  3. Test FTP: ftp localhost 2121"
echo
echo -e "${YELLOW}NOTE: Commands are displayed but NOT sent to DOOM yet.${NC}"
echo -e "${YELLOW}That will be implemented in Step 9.${NC}"
echo
echo "Press Ctrl+C to stop all services..."

# Cleanup function
cleanup() {
    echo
    echo "Stopping services..."
    kill $FTP_PID 2>/dev/null || true
    kill $WEB_PID 2>/dev/null || true
    echo "Done."
}
trap cleanup EXIT

# Wait
while true; do
    sleep 1
done