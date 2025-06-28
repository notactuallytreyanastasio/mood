#!/bin/bash
# Start DOOM with state capture (using chocolate-doom)

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# PIDs for cleanup
DOOM_PID=""
SQLITE_PID=""
CONVERTER_PID=""

cleanup() {
    echo
    echo -e "${YELLOW}Stopping services...${NC}"
    [ -n "$DOOM_PID" ] && kill $DOOM_PID 2>/dev/null || true
    [ -n "$SQLITE_PID" ] && kill $SQLITE_PID 2>/dev/null || true
    [ -n "$CONVERTER_PID" ] && kill $CONVERTER_PID 2>/dev/null || true
}
trap cleanup EXIT

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         DOOM with State Capture                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo

# Create directories
mkdir -p logs mvs_datasets

# Since we can't modify chocolate-doom, we'll simulate state export
echo -e "${YELLOW}Note: Using chocolate-doom (unmodified)${NC}"
echo -e "${YELLOW}      State export will be simulated${NC}"
echo

# Start state simulator
echo -e "${BLUE}Starting state simulator...${NC}"
python3 simulate_doom_state.py > logs/simulator.log 2>&1 &
SIMULATOR_PID=$!
sleep 2

if ps -p $SIMULATOR_PID > /dev/null; then
    echo -e "${GREEN}✓ State simulator running${NC}"
else
    echo -e "${RED}✗ Simulator failed${NC}"
    exit 1
fi

# Start SQLite capture
echo -e "${BLUE}Starting SQLite capture...${NC}"
python3 build_system/doom_state_sqlite.py > logs/sqlite.log 2>&1 &
SQLITE_PID=$!
sleep 2

if ps -p $SQLITE_PID > /dev/null; then
    echo -e "${GREEN}✓ SQLite capture running${NC}"
else
    echo -e "${RED}✗ SQLite capture failed${NC}"
    exit 1
fi

# Start MVS converter
echo -e "${BLUE}Starting MVS converter...${NC}"
python3 build_system/gamestate_to_mvs.py --monitor > logs/mvs.log 2>&1 &
CONVERTER_PID=$!
sleep 2

if ps -p $CONVERTER_PID > /dev/null; then
    echo -e "${GREEN}✓ MVS converter running${NC}"
else
    echo -e "${RED}✗ MVS converter failed${NC}"
    exit 1
fi

# Start DOOM
echo
echo -e "${BLUE}Starting DOOM...${NC}"
echo -e "${YELLOW}Press ESC in DOOM to start a new game${NC}"
echo

chocolate-doom -iwad wads/doom1.wad -window &
DOOM_PID=$!

echo
echo -e "${GREEN}All services running!${NC}"
echo
echo "Monitor with:"
echo "  • SQLite: sqlite3 doom_state.db 'SELECT COUNT(*) FROM game_state;'"
echo "  • COBOL: cat mvs_datasets/DOOM.GAMESTAT.ASCII"
echo "  • Logs: tail -f logs/*.log"
echo
echo "Press Ctrl+C to stop all services"

# Wait
while true; do
    if [ -n "$DOOM_PID" ] && ! ps -p $DOOM_PID > /dev/null; then
        echo -e "${YELLOW}DOOM has exited${NC}"
        break
    fi
    sleep 1
done