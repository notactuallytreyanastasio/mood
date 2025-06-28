#!/bin/bash
# Master control script for DOOM-COBOL integration

set -e

# Configuration
WORK_DIR="$(pwd)"
BUILD_DIR="$WORK_DIR/build_system"
INSTALL_DIR="$WORK_DIR/doom_install"
STATE_DB="$WORK_DIR/doom_state.db"
LOG_DIR="$WORK_DIR/logs"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Create directories
mkdir -p "$LOG_DIR" "$BUILD_DIR" "$INSTALL_DIR"

# PIDs for cleanup
DOOM_PID=""
SQLITE_PID=""
FTP_PID=""
BRIDGE_PID=""

# Cleanup function
cleanup() {
    echo
    echo -e "${YELLOW}Cleaning up...${NC}"
    
    [ -n "$DOOM_PID" ] && kill $DOOM_PID 2>/dev/null || true
    [ -n "$SQLITE_PID" ] && kill $SQLITE_PID 2>/dev/null || true
    [ -n "$FTP_PID" ] && kill $FTP_PID 2>/dev/null || true
    [ -n "$BRIDGE_PID" ] && kill $BRIDGE_PID 2>/dev/null || true
    
    echo "Stopped all processes"
}
trap cleanup EXIT

# Step 1: Build/Find DOOM
step1_build_doom() {
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}STEP 1: Build/Find Modified DOOM${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    
    if [ ! -f "$BUILD_DIR/setup_doom.sh" ]; then
        echo -e "${RED}Error: Build system not found${NC}"
        exit 1
    fi
    
    if [ -f "$BUILD_DIR/setup_doom.sh" ]; then
        cd "$BUILD_DIR"
        ./setup_doom.sh
        cd "$WORK_DIR"
    else
        echo -e "${RED}Build system not initialized. Setting up...${NC}"
        
        # Ensure build_system exists with our scripts
        if [ ! -f "build_system/setup_doom.sh" ]; then
            echo -e "${RED}Error: build_system/setup_doom.sh not found${NC}"
            echo "This script must be run from the DOOM project root"
            exit 1
        fi
        
        cd "$BUILD_DIR"
        ./setup_doom.sh
        cd "$WORK_DIR"
    fi
    
    # Verify we have DOOM
    if [ -f "$INSTALL_DIR/doom_path.txt" ]; then
        DOOM_PATH=$(cat "$INSTALL_DIR/doom_path.txt")
        echo -e "${GREEN}✓ Modified DOOM found at: $DOOM_PATH${NC}"
        
        # Test that it has our modifications
        if strings "$DOOM_PATH" | grep -q "X_ExportState"; then
            echo -e "${GREEN}✓ State export verified${NC}"
        else
            echo -e "${RED}✗ State export not found in binary${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ DOOM build failed${NC}"
        return 1
    fi
    
    return 0
}

# Step 2: Start SQLite capture
step2_start_sqlite() {
    echo
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}STEP 2: Start SQLite State Capture${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    
    # Make executable
    chmod +x "$BUILD_DIR/doom_state_sqlite.py"
    
    # Start SQLite capture
    echo "Starting SQLite capture on port 31337..."
    python3 "$BUILD_DIR/doom_state_sqlite.py" > "$LOG_DIR/sqlite_capture.log" 2>&1 &
    SQLITE_PID=$!
    
    sleep 2
    
    if ps -p $SQLITE_PID > /dev/null; then
        echo -e "${GREEN}✓ SQLite capture running (PID: $SQLITE_PID)${NC}"
    else
        echo -e "${RED}✗ SQLite capture failed to start${NC}"
        cat "$LOG_DIR/sqlite_capture.log"
        return 1
    fi
    
    return 0
}

# Step 3: Start DOOM
step3_start_doom() {
    echo
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}STEP 3: Start Modified DOOM${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    
    if [ ! -f "wads/doom1.wad" ]; then
        echo -e "${RED}Error: doom1.wad not found in wads/${NC}"
        return 1
    fi
    
    echo "Starting DOOM with state export..."
    "$INSTALL_DIR/run_doom.sh" > "$LOG_DIR/doom.log" 2>&1 &
    DOOM_PID=$!
    
    sleep 3
    
    if ps -p $DOOM_PID > /dev/null; then
        echo -e "${GREEN}✓ DOOM running (PID: $DOOM_PID)${NC}"
        echo "  - State export on UDP 31337"
        echo "  - Network input on UDP 31338"
        echo "  - COBOL format at /tmp/doom_state.dat"
    else
        echo -e "${RED}✗ DOOM failed to start${NC}"
        cat "$LOG_DIR/doom.log"
        return 1
    fi
    
    return 0
}

# Monitor function
monitor_system() {
    echo
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}System Running - Monitoring${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    
    echo
    echo "Press:"
    echo "  [s] - Show SQLite stats"
    echo "  [c] - Show COBOL format"
    echo "  [d] - Query database"
    echo "  [q] - Quit"
    echo
    
    while true; do
        read -n 1 -t 1 key || true
        
        case "$key" in
            s|S)
                echo
                echo "SQLite Statistics:"
                sqlite3 "$STATE_DB" "SELECT COUNT(*) as total_states FROM game_state;" 2>/dev/null || echo "No data yet"
                ;;
            c|C)
                echo
                echo "Recent COBOL format:"
                sqlite3 "$STATE_DB" "SELECT record_data FROM cobol_state ORDER BY id DESC LIMIT 10;" 2>/dev/null || echo "No data yet"
                ;;
            d|D)
                echo
                echo "Recent game states:"
                sqlite3 -header -column "$STATE_DB" \
                    "SELECT tick, health, armor, x>>16 as x, y>>16 as y, enemy_count 
                     FROM game_state ORDER BY id DESC LIMIT 5;" 2>/dev/null || echo "No data yet"
                ;;
            q|Q)
                echo
                echo "Shutting down..."
                break
                ;;
        esac
        
        # Check if processes still running
        if [ -n "$DOOM_PID" ] && ! ps -p $DOOM_PID > /dev/null; then
            echo -e "${RED}DOOM has stopped${NC}"
            break
        fi
        
        if [ -n "$SQLITE_PID" ] && ! ps -p $SQLITE_PID > /dev/null; then
            echo -e "${RED}SQLite capture has stopped${NC}"
            break
        fi
    done
}

# Main execution
main() {
    echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║          DOOM-COBOL Master Control System            ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
    echo
    
    # Step 1: Build/Find DOOM
    if ! step1_build_doom; then
        echo -e "${RED}Failed at Step 1${NC}"
        exit 1
    fi
    
    # Step 2: Start SQLite capture
    if ! step2_start_sqlite; then
        echo -e "${RED}Failed at Step 2${NC}"
        exit 1
    fi
    
    # Step 3: Start DOOM
    if ! step3_start_doom; then
        echo -e "${RED}Failed at Step 3${NC}"
        exit 1
    fi
    
    # Monitor the system
    monitor_system
    
    # Export final data
    echo
    echo "Exporting final COBOL format..."
    cd "$BUILD_DIR"
    python3 -c "
from doom_state_sqlite import DoomStateSQLite
capture = DoomStateSQLite('$STATE_DB')
capture.conn = __import__('sqlite3').connect('$STATE_DB')
capture.export_cobol_format('$WORK_DIR/final_cobol_state.txt')
"
    cd "$WORK_DIR"
    
    echo
    echo -e "${GREEN}Session complete!${NC}"
    echo "  - SQLite database: $STATE_DB"
    echo "  - COBOL format: final_cobol_state.txt"
    echo "  - Logs: $LOG_DIR/"
}

# Check Python dependencies
echo "Checking dependencies..."
python3 -c "import sqlite3" || {
    echo -e "${RED}Error: Python sqlite3 module not found${NC}"
    exit 1
}

# Run main
main