#!/bin/bash
# Run the complete DOOM-COBOL loop

echo "╔══════════════════════════════════════════════════════╗"
echo "║         DOOM-COBOL COMPLETE INTEGRATION TEST         ║" 
echo "║                                                      ║"
echo "║  DOOM → FTP → COBOL → FTP → Commands → DOOM         ║"
echo "╚══════════════════════════════════════════════════════╝"
echo

# Function to show status
show_status() {
    echo
    echo "Current Status:"
    echo "═══════════════"
    
    # Check Docker services
    if docker ps | grep -q doom-ftp-gateway; then
        echo "✓ FTP Gateway running"
    else
        echo "✗ FTP Gateway not running"
    fi
    
    if docker ps | grep -q doom-cobol-interface; then
        echo "✓ COBOL Interface running"
    else
        echo "✗ COBOL Interface not running"
    fi
    
    if docker ps | grep -q doom-bridge; then
        echo "✓ Bridge Service running"
    else
        echo "✗ Bridge Service not running"
    fi
    
    # Check state file
    if [ -f /tmp/doom_state.dat ]; then
        echo "✓ State file exists"
        echo "  Latest: $(head -1 /tmp/doom_state.dat)"
    else
        echo "✗ No state file"
    fi
}

# Cleanup function
cleanup() {
    echo
    echo "Cleaning up..."
    
    # Stop simulator if running
    [ -n "$SIM_PID" ] && kill $SIM_PID 2>/dev/null
    
    # Stop monitor if running
    [ -n "$MON_PID" ] && kill $MON_PID 2>/dev/null
    
    # Optionally stop Docker
    read -p "Stop Docker services? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose -f docker-compose-cobol.yml down
    fi
}
trap cleanup EXIT

# Main execution
main() {
    # Step 1: Start Docker services
    echo "Step 1: Starting Docker services"
    echo "────────────────────────────────"
    
    docker-compose -f docker-compose-cobol.yml up -d
    
    echo "Waiting for services to initialize..."
    sleep 10
    
    show_status
    
    # Step 2: Start state simulator
    echo
    echo "Step 2: Starting DOOM state simulator"
    echo "─────────────────────────────────────"
    
    python3 simulate_doom_state.py &
    SIM_PID=$!
    echo "State simulator started (PID: $SIM_PID)"
    
    sleep 2
    
    # Step 3: Monitor the loop
    echo
    echo "Step 3: Monitoring the feedback loop"
    echo "────────────────────────────────────"
    echo
    
    # Start command monitor
    (
        while true; do
            echo -n "."
            # Check if commands are being executed
            if echo "STATUS" | nc localhost 9999 2>/dev/null | grep -q "OK"; then
                echo -n "✓"
            fi
            sleep 1
        done
    ) &
    MON_PID=$!
    
    # Monitor logs in real-time
    echo "Monitoring system activity (press Ctrl+C to stop)..."
    echo
    echo "FTP Gateway logs:"
    echo "─────────────────"
    
    # Show logs from all services
    docker-compose -f docker-compose-cobol.yml logs -f --tail=20 &
    LOGS_PID=$!
    
    # Wait for user
    echo
    echo "The system is running!"
    echo
    echo "What's happening:"
    echo "1. Simulator writes game state to /tmp/doom_state.dat"
    echo "2. Bridge detects new state and uploads to FTP"
    echo "3. FTP gateway triggers COBOL processing"
    echo "4. COBOL analyzes state and generates commands"
    echo "5. Bridge downloads commands and sends to port 9999"
    echo "6. Commands would control DOOM (if it were running)"
    echo
    echo "Press Enter to see current state, or Ctrl+C to stop..."
    
    while true; do
        read
        show_status
        
        echo
        echo "Latest commands processed:"
        docker-compose -f docker-compose-cobol.yml logs --tail=5 ftp-gateway | grep "COBOL AI:"
    done
}

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not installed!"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not installed!"
    exit 1
fi

echo "✓ Prerequisites satisfied"

# Run main
main