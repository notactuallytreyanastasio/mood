#!/bin/bash
# DOOM-COBOL Demo Script
# Shows the complete system in action

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

clear

echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║${NC}                  ${YELLOW}DOOM-COBOL DEMO${NC}                            ${RED}║${NC}"
echo -e "${RED}║${NC}         ${BLUE}1960s Mainframe Technology Plays 1993 DOOM${NC}           ${RED}║${NC}"
echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step counter
STEP=0

step() {
    STEP=$((STEP + 1))
    echo -e "\n${GREEN}Step $STEP:${NC} $1"
    echo "────────────────────────────────────────────────────"
}

press_enter() {
    echo -e "\n${YELLOW}Press Enter to continue...${NC}"
    read
}

# Introduction
echo -e "${BLUE}Welcome to the DOOM-COBOL demonstration!${NC}"
echo ""
echo "This demo will show you how COBOL programs running in Docker"
echo "containers can control the classic game DOOM through a series"
echo "of batch-processing style commands."
echo ""
echo "What you'll see:"
echo "  • Docker containers providing mainframe-style processing"
echo "  • COBOL command interface accepting high-level commands"
echo "  • Mock MVS datasets storing game state"
echo "  • AI decision making in the style of 1960s business logic"
echo "  • Real keyboard/mouse control of DOOM (if running)"

press_enter

# Check system
step "Checking system requirements"

echo -n "Docker: "
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} Please install Docker"
    exit 1
fi

echo -n "Python 3: "
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC} Please install Python 3"
    exit 1
fi

echo -n "DOOM: "
if command -v chocolate-doom &> /dev/null; then
    echo -e "${GREEN}✓${NC} chocolate-doom found"
elif command -v gzdoom &> /dev/null; then
    echo -e "${GREEN}✓${NC} gzdoom found"
else
    echo -e "${YELLOW}⚠${NC} No DOOM found (demo will still work)"
fi

press_enter

# Start services
step "Starting Docker services"

echo "Starting COBOL interface and web dashboard..."
make -f Makefile.simple up-simple

# Wait for services
echo -n "Waiting for services"
for i in {1..10}; do
    if echo "STATUS" | nc localhost 9999 2>/dev/null | grep -q "OK"; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

echo ""
echo -e "${GREEN}Services running:${NC}"
echo "  • COBOL Interface: localhost:9999"
echo "  • Web Dashboard: http://localhost:8080"

press_enter

# Show status
step "Testing COBOL interface"

echo "Sending STATUS command..."
echo -e "${BLUE}Command:${NC} echo 'STATUS' | nc localhost 9999"
echo -e "${BLUE}Response:${NC}"
echo "STATUS" | nc localhost 9999

press_enter

# Demonstrate commands
step "Demonstrating COBOL commands"

echo "The COBOL interface accepts these commands:"
echo ""
echo "  ${BLUE}Movement:${NC}"
echo "    MOVE FORWARD|BACK|LEFT|RIGHT [seconds]"
echo ""
echo "  ${BLUE}Combat:${NC}"
echo "    TURN LEFT|RIGHT [degrees]"
echo "    SHOOT [count]"
echo ""
echo "  ${BLUE}Interaction:${NC}"
echo "    USE"
echo "    WEAPON [1-7]"

press_enter

# Send test commands
step "Sending test commands"

commands=(
    "MOVE FORWARD 2:Moving forward for 2 seconds"
    "TURN RIGHT 90:Turning right 90 degrees"
    "SHOOT 3:Firing weapon 3 times"
    "MOVE BACK 1:Backing up for safety"
    "USE:Opening door or activating switch"
)

for cmd_desc in "${commands[@]}"; do
    IFS=':' read -r cmd desc <<< "$cmd_desc"
    echo -e "\n${BLUE}$desc${NC}"
    echo "Command: $cmd"
    echo -n "Response: "
    echo "$cmd" | nc localhost 9999
    sleep 1
done

press_enter

# Show AI logic
step "Demonstrating AI decision logic"

echo "The COBOL AI makes decisions based on game state:"
echo ""
echo -e "${BLUE}SURVIVAL MODE${NC} (Health < 30)"
echo "  • Retreat to find health"
echo "  • Avoid combat"
echo ""
echo -e "${BLUE}COMBAT MODE${NC} (Taking damage)"
echo "  • Turn to face threat"
echo "  • Return fire"
echo "  • Strafe to avoid damage"
echo ""
echo -e "${BLUE}EXPLORE MODE${NC} (Safe)"
echo "  • Move forward"
echo "  • Check corners"
echo "  • Open doors"

press_enter

# Start AI demo
step "Running AI demonstration"

echo "Starting 30-second AI demo..."
echo "(The AI will make tactical decisions automatically)"
echo ""

# Run AI for 30 seconds
timeout 30 bash -c '
    CYCLE=0
    while true; do
        CYCLE=$((CYCLE + 1))
        echo "AI Cycle $CYCLE"
        
        # Simulate different scenarios
        case $((CYCLE % 3)) in
            0)
                echo "  → Exploring: Moving forward"
                echo "MOVE FORWARD 1" | nc localhost 9999
                ;;
            1)
                echo "  → Combat: Engaging enemy"
                echo "TURN RIGHT 45" | nc localhost 9999
                sleep 0.5
                echo "SHOOT 2" | nc localhost 9999
                ;;
            2)
                echo "  → Tactical: Checking surroundings"
                echo "TURN LEFT 90" | nc localhost 9999
                sleep 0.5
                echo "MOVE LEFT 0.5" | nc localhost 9999
                ;;
        esac
        
        sleep 2
    done
' || true

echo -e "\n${GREEN}AI demo complete!${NC}"

press_enter

# Show architecture
step "System architecture"

cat << 'EOF'
The DOOM-COBOL system architecture:

┌─────────────────┐         ┌──────────────────┐
│  Your Commands  │────────▶│ COBOL Interface  │
│  (Port 9999)    │         │   (Docker)       │
└─────────────────┘         └────────┬─────────┘
                                     │
                            ┌────────▼─────────┐
                            │   Mock MVS       │
                            │ (Game State DB)  │
                            └────────┬─────────┘
                                     │
                            ┌────────▼─────────┐
                            │   AI Logic       │
                            │ (COBOL-style)    │
                            └────────┬─────────┘
                                     │
                            ┌────────▼─────────┐
                            │ Keyboard/Mouse   │
                            │   Control        │
                            └────────┬─────────┘
                                     │
                                     ▼
                               🎮 DOOM 🎮
EOF

press_enter

# Cleanup options
step "Demo complete!"

echo -e "${GREEN}The DOOM-COBOL system is now running!${NC}"
echo ""
echo "You can:"
echo "  1. Send more commands: echo 'MOVE FORWARD' | nc localhost 9999"
echo "  2. View the dashboard: http://localhost:8080"
echo "  3. Start DOOM and watch it respond to commands"
echo "  4. Run the AI loop: ./start_ai_loop.sh"
echo ""
echo -e "${YELLOW}To stop all services:${NC} make -f Makefile.simple down-simple"
echo ""
echo -e "${BLUE}Thank you for trying DOOM-COBOL!${NC}"
echo "Where mainframe batch processing meets demon slaying!"

# Keep services running
echo -e "\n${YELLOW}Services will keep running. Press Ctrl+C to exit.${NC}"
trap "echo -e '\n${RED}Exiting demo...${NC}'" EXIT
while true; do sleep 1; done