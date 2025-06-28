#!/bin/bash
# Simple demo of DOOM-COBOL flow

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Directories
MVS_DIR="mvs_datasets"
LOG_DIR="logs"

# PIDs
SQLITE_PID=""
FTP_PID=""
WEB_PID=""

cleanup() {
    echo -e "${YELLOW}Cleaning up...${NC}"
    [ -n "$SQLITE_PID" ] && kill $SQLITE_PID 2>/dev/null || true
    [ -n "$FTP_PID" ] && kill $FTP_PID 2>/dev/null || true
    [ -n "$WEB_PID" ] && kill $WEB_PID 2>/dev/null || true
}
trap cleanup EXIT

clear

echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║        DOOM-COBOL Simple Flow Demo                  ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
echo

mkdir -p "$LOG_DIR" "$MVS_DIR"

# Step 1: Start state simulator
echo -e "${BLUE}Step 1: Starting DOOM state simulator...${NC}"
python3 simulate_doom_simple.py > "$LOG_DIR/simulator.log" 2>&1 &
SIM_PID=$!
sleep 2

if ps -p $SIM_PID > /dev/null; then
    echo -e "${GREEN}✓ State simulator running${NC}"
    echo "  Sending game state to UDP port 31337"
else
    echo -e "${RED}✗ Simulator failed${NC}"
    exit 1
fi

# Step 2: Start SQLite capture
echo
echo -e "${BLUE}Step 2: Starting SQLite capture...${NC}"
python3 build_system/doom_state_sqlite.py > "$LOG_DIR/sqlite.log" 2>&1 &
SQLITE_PID=$!
sleep 2

if ps -p $SQLITE_PID > /dev/null; then
    echo -e "${GREEN}✓ SQLite capture running${NC}"
    echo "  Database: doom_state.db"
else
    echo -e "${RED}✗ SQLite capture failed${NC}"
    exit 1
fi

# Step 3: Create some test data
echo
echo -e "${BLUE}Step 3: Generating test game states...${NC}"
sleep 3

# Check database
COUNT=$(sqlite3 doom_state.db "SELECT COUNT(*) FROM game_state;" 2>/dev/null || echo "0")
echo -e "${GREEN}✓ Captured $COUNT game states${NC}"

# Show sample
echo
echo "Sample game state:"
sqlite3 -header -column doom_state.db \
    "SELECT tick, health, armor, x>>16 as x, y>>16 as y 
     FROM game_state ORDER BY id DESC LIMIT 1;" 2>/dev/null || echo "No data yet"

# Step 4: Convert to MVS
echo
echo -e "${BLUE}Step 4: Converting to MVS dataset format...${NC}"
python3 build_system/gamestate_to_mvs.py --once

if [ -f "$MVS_DIR/DOOM.GAMESTAT.ASCII" ]; then
    echo -e "${GREEN}✓ MVS dataset created${NC}"
    echo
    echo "COBOL format (first 3 records):"
    head -3 "$MVS_DIR/DOOM.GAMESTAT.ASCII"
fi

# Step 5: Start FTP Gateway
echo
echo -e "${BLUE}Step 5: Starting FTP Gateway...${NC}"
python3 ftp-gateway/mvs_ftp_gateway.py > "$LOG_DIR/ftp.log" 2>&1 &
FTP_PID=$!
sleep 2

if ps -p $FTP_PID > /dev/null; then
    echo -e "${GREEN}✓ FTP Gateway running on port 2121${NC}"
else
    echo -e "${RED}✗ FTP Gateway failed${NC}"
fi

# Step 6: Simulate COBOL commands
echo
echo -e "${BLUE}Step 6: Simulating COBOL AI commands...${NC}"
cat > "$MVS_DIR/DOOM.COMMANDS.ASCII" << 'EOF'
COMMAND MOVE    FORWARD 00209EXPLORATION MODE                               
COMMAND TURN    RIGHT   00453SCAN FOR ENEMIES                               
COMMAND SHOOT           00015ENEMY DETECTED                                 
COMMAND MOVE    BACK    00209TACTICAL RETREAT                               
COMMAND WAIT            00107PROCESSING THREAT                              
EOF
echo -e "${GREEN}✓ Created 5 COBOL commands${NC}"

# Step 7: Start Web Server
echo
echo -e "${BLUE}Step 7: Starting Web Server...${NC}"
python3 web-ui/cobol_action_server.py > "$LOG_DIR/web.log" 2>&1 &
WEB_PID=$!
sleep 3

if ps -p $WEB_PID > /dev/null; then
    echo -e "${GREEN}✓ Web Server running${NC}"
    echo -e "${YELLOW}  Open http://localhost:8080 to see commands${NC}"
else
    echo -e "${RED}✗ Web Server failed${NC}"
fi

# Summary
echo
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Flow Complete!${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo
echo "What's happening:"
echo "  1. State simulator → UDP packets → SQLite"
echo "  2. SQLite → MVS datasets (COBOL format)"
echo "  3. FTP Gateway ready for mainframe"
echo "  4. COBOL commands → Web interface"
echo
echo "Services:"
echo "  • SQLite DB: doom_state.db"
echo "  • FTP Server: localhost:2121"
echo "  • Web UI: http://localhost:8080"
echo
echo "To run with real DOOM:"
echo "  chocolate-doom -iwad wads/doom1.wad -window"
echo
echo "Press Ctrl+C to stop all services"

# Kill simulator after demo data
sleep 5
kill $SIM_PID 2>/dev/null || true

# Wait
while true; do
    sleep 1
done