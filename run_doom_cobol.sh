#!/bin/bash
# DOOM-COBOL Runner
# Starts everything needed for COBOL to control DOOM

set -e

echo "╔══════════════════════════════════════════════╗"
echo "║          DOOM-COBOL CONTROL SYSTEM           ║"
echo "║   Where 1960s Mainframes Meet 1990s Gaming   ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Function to check dependencies
check_deps() {
    local missing=0
    
    echo "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        echo "  ✗ Docker not found"
        missing=1
    else
        echo "  ✓ Docker found"
    fi
    
    if ! command -v python3 &> /dev/null; then
        echo "  ✗ Python 3 not found"
        missing=1
    else
        echo "  ✓ Python 3 found"
    fi
    
    if ! command -v nc &> /dev/null; then
        echo "  ✗ netcat not found"
        missing=1
    else
        echo "  ✓ netcat found"
    fi
    
    # Check for DOOM
    local doom_found=0
    for doom_exe in chocolate-doom gzdoom doom; do
        if command -v $doom_exe &> /dev/null; then
            echo "  ✓ DOOM found: $doom_exe"
            doom_found=1
            break
        fi
    done
    
    if [ $doom_found -eq 0 ]; then
        echo "  ✗ DOOM not found (install chocolate-doom)"
        missing=1
    fi
    
    return $missing
}

# Function to start services
start_services() {
    echo ""
    echo "Starting Docker services..."
    
    # Start the containers
    make -f Makefile.simple up-simple
    
    # Wait for services
    echo "Waiting for services to initialize..."
    local attempts=0
    while ! echo "STATUS" | nc localhost 9999 2>/dev/null | grep -q "OK"; do
        sleep 1
        attempts=$((attempts + 1))
        if [ $attempts -gt 30 ]; then
            echo "ERROR: Services failed to start!"
            return 1
        fi
    done
    
    echo "  ✓ COBOL interface ready on port 9999"
    echo "  ✓ Web dashboard ready at http://localhost:8080"
}

# Function to create command relay
create_relay() {
    # Create a FIFO for command relay
    COMMAND_PIPE="/tmp/doom-cobol-pipe"
    rm -f $COMMAND_PIPE
    mkfifo $COMMAND_PIPE
    
    # Start relay process
    (
        while true; do
            if read cmd < $COMMAND_PIPE; then
                echo "$cmd" | nc localhost 9999
            fi
        done
    ) &
    RELAY_PID=$!
    echo "  ✓ Command relay started (PID: $RELAY_PID)"
}

# Function to show usage
show_usage() {
    echo ""
    echo "════════════════════════════════════════════════"
    echo "SYSTEM READY! Here's how to use it:"
    echo ""
    echo "1. Start DOOM (in another terminal):"
    echo "   chocolate-doom -window -geometry 640x480"
    echo ""
    echo "2. Send COBOL commands:"
    echo "   echo 'MOVE FORWARD 2' | nc localhost 9999"
    echo "   echo 'TURN RIGHT 90' | nc localhost 9999"
    echo "   echo 'SHOOT 3' | nc localhost 9999"
    echo ""
    echo "3. View dashboard:"
    echo "   open http://localhost:8080"
    echo ""
    echo "4. Run AI loop:"
    echo "   ./start_ai_loop.sh"
    echo "════════════════════════════════════════════════"
}

# Cleanup function
cleanup() {
    echo ""
    echo "Shutting down DOOM-COBOL system..."
    
    # Kill relay
    [ -n "$RELAY_PID" ] && kill $RELAY_PID 2>/dev/null
    
    # Remove pipe
    rm -f /tmp/doom-cobol-pipe
    
    # Stop Docker services
    make -f Makefile.simple down-simple
    
    echo "Shutdown complete."
}

# Main execution
main() {
    # Check dependencies
    if ! check_deps; then
        echo ""
        echo "ERROR: Missing dependencies. Please install required software."
        exit 1
    fi
    
    # Set up cleanup
    trap cleanup EXIT INT TERM
    
    # Start services
    if ! start_services; then
        exit 1
    fi
    
    # Create command relay
    create_relay
    
    # Show usage
    show_usage
    
    # Keep running
    echo ""
    echo "Press Ctrl+C to shutdown..."
    
    # Monitor loop
    while true; do
        sleep 5
        
        # Check if services are still running
        if ! docker ps | grep -q doom-cobol-interface; then
            echo "WARNING: COBOL interface stopped!"
            break
        fi
    done
}

# Run main
main