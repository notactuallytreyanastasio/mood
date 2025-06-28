#!/bin/bash
# Demonstrate the complete DOOM-COBOL feedback loop

echo "╔══════════════════════════════════════════════════════╗"
echo "║          DOOM-COBOL FEEDBACK LOOP DEMO              ║"
echo "║                                                      ║"
echo "║  Showing: DOOM → FTP → COBOL → FTP → Commands       ║"
echo "╚══════════════════════════════════════════════════════╝"
echo

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Create demo state writer
write_state() {
    local health=$1
    local tick=$2
    
    cat > /tmp/doom_state.dat << EOF
STATE $(printf "%08d" $tick) 01
PLAYER+0001024+0001024+0000000+090$(printf "%03d" $health)050
AMMO  0050002001000040 2
EOF
}

# Show what's happening
show_flow() {
    echo
    echo -e "${BLUE}┌─────────────────────────────────────────┐${NC}"
    echo -e "${BLUE}│         DOOM-COBOL Data Flow            │${NC}"
    echo -e "${BLUE}├─────────────────────────────────────────┤${NC}"
    echo -e "${BLUE}│                                         │${NC}"
    echo -e "${BLUE}│  1. DOOM writes → /tmp/doom_state.dat   │${NC}"
    echo -e "${BLUE}│           ↓                             │${NC}"
    echo -e "${BLUE}│  2. Bridge reads state                  │${NC}"
    echo -e "${BLUE}│           ↓                             │${NC}"
    echo -e "${BLUE}│  3. FTP upload → DOOM.GAMESTAT          │${NC}"
    echo -e "${BLUE}│           ↓                             │${NC}"
    echo -e "${BLUE}│  4. COBOL analyzes state                │${NC}"
    echo -e "${BLUE}│           ↓                             │${NC}"
    echo -e "${BLUE}│  5. COBOL writes → DOOM.COMMANDS        │${NC}"
    echo -e "${BLUE}│           ↓                             │${NC}"
    echo -e "${BLUE}│  6. FTP download commands               │${NC}"
    echo -e "${BLUE}│           ↓                             │${NC}"
    echo -e "${BLUE}│  7. Send to port 9999                   │${NC}"
    echo -e "${BLUE}│           ↓                             │${NC}"
    echo -e "${BLUE}│  8. DOOM executes commands              │${NC}"
    echo -e "${BLUE}│                                         │${NC}"
    echo -e "${BLUE}└─────────────────────────────────────────┘${NC}"
}

# Main demo
main() {
    show_flow
    
    echo
    echo "Starting services with Docker Compose..."
    docker-compose -f docker-compose-cobol.yml up -d
    
    echo "Waiting for services to initialize..."
    sleep 10
    
    # Check services
    echo
    echo -e "${GREEN}Service Status:${NC}"
    docker-compose -f docker-compose-cobol.yml ps
    
    echo
    echo -e "${YELLOW}═══════════════════════════════════════════${NC}"
    echo -e "${YELLOW}Starting DOOM-COBOL Loop Demonstration${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════${NC}"
    
    # Demo scenarios
    scenarios=(
        "25:CRITICAL - Low health, should retreat"
        "45:CAUTIOUS - Medium health, careful advance"
        "85:AGGRESSIVE - High health, explore and attack"
    )
    
    tick=1000
    for scenario in "${scenarios[@]}"; do
        IFS=':' read -r health description <<< "$scenario"
        
        echo
        echo -e "${GREEN}Scenario: $description${NC}"
        echo "─────────────────────────────────────"
        
        # Write state
        echo "1. Writing game state (health=$health)..."
        write_state $health $tick
        echo "   State written to /tmp/doom_state.dat"
        
        # Show state
        echo "2. Current state:"
        cat /tmp/doom_state.dat | sed 's/^/   /'
        
        # Wait for processing
        echo "3. Waiting for COBOL processing..."
        sleep 5
        
        # Show COBOL decision
        echo "4. COBOL AI decision:"
        docker-compose -f docker-compose-cobol.yml logs --tail=20 ftp-gateway | \
            grep "COBOL AI:" | tail -3 | sed 's/^/   /'
        
        # Show commands
        echo "5. Commands generated:"
        docker-compose -f docker-compose-cobol.yml logs --tail=20 ftp-gateway | \
            grep "Executed:" | tail -3 | sed 's/^/   /'
        
        tick=$((tick + 100))
        
        echo
        read -p "Press Enter for next scenario..."
    done
    
    # Show continuous operation
    echo
    echo -e "${YELLOW}═══════════════════════════════════════════${NC}"
    echo -e "${YELLOW}Continuous Operation Demo${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════${NC}"
    echo
    echo "Starting continuous state updates..."
    echo "(Press Ctrl+C to stop)"
    echo
    
    # Monitor logs in background
    docker-compose -f docker-compose-cobol.yml logs -f --tail=0 | \
        grep -E "(COBOL AI:|Executed:|Processing new game state)" &
    LOGS_PID=$!
    
    # Simulate changing game state
    health=100
    while true; do
        # Update state
        write_state $health $tick
        echo -ne "\rGame tick: $tick, Health: $health  "
        
        # Simulate damage/healing
        if [ $((RANDOM % 3)) -eq 0 ]; then
            health=$((health - RANDOM % 20))
            [ $health -lt 10 ] && health=10
        fi
        if [ $((RANDOM % 5)) -eq 0 ]; then
            health=$((health + 10))
            [ $health -gt 100 ] && health=100
        fi
        
        tick=$((tick + 1))
        sleep 2
    done
}

# Cleanup
cleanup() {
    echo
    echo
    echo "Cleaning up..."
    [ -n "$LOGS_PID" ] && kill $LOGS_PID 2>/dev/null
    
    read -p "Stop Docker services? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose -f docker-compose-cobol.yml down
    fi
}
trap cleanup EXIT

# Run demo
main