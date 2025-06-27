#!/bin/bash
# DOOM-COBOL AI Loop
# Runs the AI decision loop continuously

echo "Starting DOOM-COBOL AI Loop..."
echo ""

# Check if interface is running
if ! echo "STATUS" | nc localhost 9999 2>/dev/null | grep -q "OK"; then
    echo "ERROR: COBOL interface not running!"
    echo "Please run ./run_doom_cobol.sh first"
    exit 1
fi

# AI decision loop
AI_CYCLE=0
LAST_HEALTH=100

echo "AI Brain activated - Making tactical decisions..."
echo "══════════════════════════════════════════════"

while true; do
    AI_CYCLE=$((AI_CYCLE + 1))
    
    # Get current game state
    STATE=$(echo "STATUS" | nc localhost 9999 2>/dev/null)
    
    if [[ $STATE == *"OK:"* ]]; then
        # Extract health from state (mock data for now)
        HEALTH=$(echo $STATE | grep -o 'Health=[0-9]*' | cut -d= -f2 || echo "100")
        
        echo ""
        echo "Cycle $AI_CYCLE - Health: $HEALTH"
        
        # Make decisions based on state
        if [ "$HEALTH" -lt "30" ]; then
            echo "  → SURVIVAL MODE: Low health detected!"
            echo "MOVE BACK 2" | nc localhost 9999
            sleep 2
            echo "TURN RIGHT 180" | nc localhost 9999
            sleep 1
            
        elif [ "$HEALTH" -lt "$LAST_HEALTH" ]; then
            echo "  → COMBAT MODE: Taking damage!"
            echo "TURN RIGHT 45" | nc localhost 9999
            sleep 0.5
            echo "SHOOT 3" | nc localhost 9999
            sleep 1
            echo "MOVE LEFT 1" | nc localhost 9999
            sleep 1
            
        else
            # Exploration pattern
            PATTERN=$((AI_CYCLE % 4))
            case $PATTERN in
                0)
                    echo "  → EXPLORE: Moving forward"
                    echo "MOVE FORWARD 2" | nc localhost 9999
                    ;;
                1)
                    echo "  → EXPLORE: Checking right"
                    echo "TURN RIGHT 90" | nc localhost 9999
                    sleep 0.5
                    echo "MOVE FORWARD 1" | nc localhost 9999
                    ;;
                2)
                    echo "  → EXPLORE: Checking surroundings"
                    echo "TURN LEFT 180" | nc localhost 9999
                    ;;
                3)
                    echo "  → EXPLORE: Opening doors"
                    echo "USE" | nc localhost 9999
                    sleep 0.5
                    echo "MOVE FORWARD 1" | nc localhost 9999
                    ;;
            esac
        fi
        
        LAST_HEALTH=$HEALTH
        
    else
        echo "  ⚠ Cannot read game state"
    fi
    
    # Wait before next cycle
    sleep 2
done