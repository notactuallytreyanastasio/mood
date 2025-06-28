#!/bin/bash
# Demo the complete DOOM-COBOL flow with live state capture

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Directories
WORK_DIR="$(pwd)"
BUILD_DIR="$WORK_DIR/build_system"
MVS_DIR="$WORK_DIR/mvs_datasets"
LOG_DIR="$WORK_DIR/logs"

# PIDs for cleanup
DOOM_PID=""
SQLITE_PID=""
CONVERTER_PID=""
FTP_PID=""
WEB_PID=""

# Cleanup function
cleanup() {
    echo
    echo -e "${YELLOW}Cleaning up...${NC}"
    [ -n "$DOOM_PID" ] && kill $DOOM_PID 2>/dev/null || true
    [ -n "$SQLITE_PID" ] && kill $SQLITE_PID 2>/dev/null || true
    [ -n "$CONVERTER_PID" ] && kill $CONVERTER_PID 2>/dev/null || true
    [ -n "$FTP_PID" ] && kill $FTP_PID 2>/dev/null || true
    [ -n "$WEB_PID" ] && kill $WEB_PID 2>/dev/null || true
    echo "All processes stopped."
}
trap cleanup EXIT

clear

echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     DOOM-COBOL Complete Flow Demonstration          ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
echo
echo "This demo shows the complete flow:"
echo "  1. DOOM exports game state via UDP"
echo "  2. SQLite captures and stores state"
echo "  3. State converted to MVS dataset format"
echo "  4. COBOL AI would process via FTP"
echo "  5. Commands appear in web interface"
echo
read -p "Press Enter to start the demo..."

# Create directories
mkdir -p "$LOG_DIR" "$MVS_DIR"

# Step 1: Build/Find modified DOOM
echo
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}STEP 1: Setting up Modified DOOM${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"

if [ -f "$BUILD_DIR/setup_doom.sh" ]; then
    echo "Checking for modified DOOM..."
    
    # Quick check without full build
    if [ -f "doom_install/doom_path.txt" ]; then
        DOOM_PATH=$(cat doom_install/doom_path.txt)
        if [ -f "$DOOM_PATH" ] && strings "$DOOM_PATH" 2>/dev/null | grep -q "X_ExportState"; then
            echo -e "${GREEN}✓ Modified DOOM found at: $DOOM_PATH${NC}"
        else
            echo -e "${YELLOW}! Running setup_doom.sh to build/patch DOOM...${NC}"
            cd "$BUILD_DIR"
            ./setup_doom.sh
            cd "$WORK_DIR"
        fi
    else
        echo -e "${YELLOW}! First time setup - building DOOM...${NC}"
        cd "$BUILD_DIR"
        ./setup_doom.sh
        cd "$WORK_DIR"
    fi
else
    echo -e "${RED}Error: Build system not found${NC}"
    exit 1
fi

echo
read -p "Press Enter to start SQLite capture..."

# Step 2: Start SQLite capture
echo
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}STEP 2: Starting SQLite State Capture${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"

echo "Starting SQLite capture on UDP port 31337..."
python3 "$BUILD_DIR/doom_state_sqlite.py" > "$LOG_DIR/sqlite_capture.log" 2>&1 &
SQLITE_PID=$!

sleep 2

if ps -p $SQLITE_PID > /dev/null; then
    echo -e "${GREEN}✓ SQLite capture running (PID: $SQLITE_PID)${NC}"
    echo "  - Listening on UDP port 31337"
    echo "  - Database: doom_state.db"
    echo "  - COBOL format: /tmp/doom_state.dat"
else
    echo -e "${RED}✗ SQLite capture failed${NC}"
    cat "$LOG_DIR/sqlite_capture.log"
    exit 1
fi

echo
read -p "Press Enter to start MVS dataset converter..."

# Step 3: Start MVS converter
echo
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}STEP 3: Starting MVS Dataset Converter${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"

echo "Starting game state to MVS converter..."
python3 "$BUILD_DIR/gamestate_to_mvs.py" --monitor > "$LOG_DIR/mvs_converter.log" 2>&1 &
CONVERTER_PID=$!

sleep 2

if ps -p $CONVERTER_PID > /dev/null; then
    echo -e "${GREEN}✓ MVS converter running (PID: $CONVERTER_PID)${NC}"
    echo "  - Monitoring SQLite for new states"
    echo "  - Creating EBCDIC datasets in: $MVS_DIR/"
else
    echo -e "${RED}✗ MVS converter failed${NC}"
    exit 1
fi

echo
read -p "Press Enter to start FTP Gateway..."

# Step 4: Start FTP Gateway
echo
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}STEP 4: Starting MVS FTP Gateway${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"

echo "Starting FTP gateway for MVS datasets..."
python3 ftp-gateway/mvs_ftp_gateway.py > "$LOG_DIR/ftp_gateway.log" 2>&1 &
FTP_PID=$!

sleep 2

if ps -p $FTP_PID > /dev/null; then
    echo -e "${GREEN}✓ FTP Gateway running (PID: $FTP_PID)${NC}"
    echo "  - FTP Server: localhost:2121"
    echo "  - User: doom / doomguy"
    echo "  - Datasets: /doom/gamestate/, /doom/commands/"
else
    echo -e "${RED}✗ FTP Gateway failed${NC}"
    exit 1
fi

echo
read -p "Press Enter to start Web Server..."

# Step 5: Start Web Server
echo
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}STEP 5: Starting COBOL Action Web Server${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"

echo "Starting web server for action monitoring..."
python3 web-ui/cobol_action_server.py > "$LOG_DIR/web_server.log" 2>&1 &
WEB_PID=$!

sleep 3

if ps -p $WEB_PID > /dev/null; then
    echo -e "${GREEN}✓ Web Server running (PID: $WEB_PID)${NC}"
    echo "  - Web Interface: http://localhost:8080"
    echo "  - API Endpoint: http://localhost:8080/api"
else
    echo -e "${RED}✗ Web Server failed${NC}"
    exit 1
fi

echo
echo -e "${MAGENTA}═══════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}All services running! Now let's start DOOM...${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════${NC}"
echo
read -p "Press Enter to start DOOM with state export..."

# Step 6: Start DOOM
echo
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}STEP 6: Starting Modified DOOM${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"

if [ ! -f "wads/doom1.wad" ]; then
    echo -e "${RED}Error: doom1.wad not found in wads/${NC}"
    exit 1
fi

echo "Starting DOOM..."
echo -e "${YELLOW}NOTE: DOOM will open in a new window${NC}"
echo -e "${YELLOW}      Press ESC in DOOM to start a new game${NC}"
echo

# Start DOOM
if [ -f "doom_install/run_doom.sh" ]; then
    ./doom_install/run_doom.sh > "$LOG_DIR/doom.log" 2>&1 &
    DOOM_PID=$!
else
    # Fallback
    DOOM_PATH=$(cat doom_install/doom_path.txt)
    "$DOOM_PATH" -iwad wads/doom1.wad -window -geometry 640x480 > "$LOG_DIR/doom.log" 2>&1 &
    DOOM_PID=$!
fi

sleep 3

if ps -p $DOOM_PID > /dev/null; then
    echo -e "${GREEN}✓ DOOM running (PID: $DOOM_PID)${NC}"
else
    echo -e "${RED}✗ DOOM failed to start${NC}"
    cat "$LOG_DIR/doom.log"
    exit 1
fi

# Step 7: Monitor the flow
echo
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}LIVE MONITORING - Watch the Data Flow!${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo
echo "Services Running:"
echo "  • DOOM → UDP 31337 → SQLite → MVS Datasets"
echo "  • FTP Gateway serving datasets on port 2121"
echo "  • Web Server showing actions on port 8080"
echo
echo -e "${YELLOW}Open http://localhost:8080 in your browser!${NC}"
echo
echo "Commands:"
echo "  [s] - Show SQLite stats"
echo "  [d] - Display recent game states"
echo "  [m] - Show MVS datasets"
echo "  [c] - Simulate COBOL commands"
echo "  [q] - Quit"
echo

# Monitoring loop
while true; do
    read -n 1 -t 1 key || true
    
    case "$key" in
        s|S)
            echo
            echo -e "${BLUE}SQLite Statistics:${NC}"
            sqlite3 doom_state.db "SELECT COUNT(*) as states, MAX(tick) as latest_tick FROM game_state;" 2>/dev/null || echo "No data yet"
            echo
            ;;
            
        d|D)
            echo
            echo -e "${BLUE}Recent Game States:${NC}"
            sqlite3 -header -column doom_state.db \
                "SELECT id, tick, health, armor, x>>16 as x, y>>16 as y, enemy_count 
                 FROM game_state ORDER BY id DESC LIMIT 5;" 2>/dev/null || echo "No data yet"
            echo
            ;;
            
        m|M)
            echo
            echo -e "${BLUE}MVS Datasets:${NC}"
            ls -la "$MVS_DIR"/*.ASCII 2>/dev/null | tail -5 || echo "No datasets yet"
            
            if [ -f "$MVS_DIR/DOOM.GAMESTAT.ASCII" ]; then
                echo
                echo "Latest GAMESTAT (first 3 records):"
                head -3 "$MVS_DIR/DOOM.GAMESTAT.ASCII"
            fi
            echo
            ;;
            
        c|C)
            echo
            echo -e "${BLUE}Simulating COBOL Commands:${NC}"
            cat > "$MVS_DIR/DOOM.COMMANDS.ASCII" << EOF
COMMAND MOVE    FORWARD 00309EXPLORATION MODE                               
COMMAND TURN    RIGHT   00453SCAN FOR ENEMIES                               
COMMAND SHOOT           00015ENEMY DETECTED                                 
COMMAND MOVE    BACK    00209TACTICAL RETREAT                               
EOF
            echo "Added 4 simulated COBOL commands"
            echo "Check http://localhost:8080 to see them!"
            echo
            ;;
            
        q|Q)
            echo
            echo "Shutting down demo..."
            break
            ;;
    esac
    
    # Check processes
    if [ -n "$DOOM_PID" ] && ! ps -p $DOOM_PID > /dev/null; then
        echo -e "${RED}DOOM has stopped${NC}"
        break
    fi
done

echo
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Demo Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo
echo "What you witnessed:"
echo "  1. DOOM exported game state via UDP"
echo "  2. SQLite captured $(sqlite3 doom_state.db "SELECT COUNT(*) FROM game_state;" 2>/dev/null || echo "many") game states"
echo "  3. States converted to MVS dataset format"
echo "  4. FTP gateway ready for mainframe connection"
echo "  5. Web interface showing COBOL commands"
echo
echo "Files created:"
echo "  - doom_state.db - SQLite database"
echo "  - $MVS_DIR/ - MVS datasets"
echo "  - /tmp/doom_state.dat - COBOL format"
echo
echo -e "${YELLOW}NOTE: Step 9 (sending commands back to DOOM) not implemented yet${NC}"