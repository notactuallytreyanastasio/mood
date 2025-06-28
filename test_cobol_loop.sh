#!/bin/bash
# Test the complete DOOM → FTP → COBOL → FTP → DOOM loop

set -e

echo "======================================"
echo "DOOM-COBOL Complete Loop Test"
echo "======================================"

# Create test state file
create_test_state() {
    echo "Creating test game state..."
    cat > /tmp/doom_state.dat << EOF
STATE 00001234 01
PLAYER+0001024+0001024+0000000+090${1:-075}050
AMMO  0050002001000040 2
EOF
    echo "Created state with health: ${1:-75}"
}

# Check services
check_services() {
    echo
    echo "Checking services..."
    
    # Check FTP
    if nc -z localhost 2121 2>/dev/null; then
        echo "✓ FTP server on port 2121"
    else
        echo "✗ FTP server not running"
        return 1
    fi
    
    # Check COBOL interface
    if nc -z localhost 9999 2>/dev/null; then
        echo "✓ COBOL interface on port 9999"
    else
        echo "✗ COBOL interface not running"
        return 1
    fi
    
    return 0
}

# Start services
start_services() {
    echo
    echo "Starting Docker services..."
    docker-compose -f docker-compose-cobol.yml up -d
    
    echo "Waiting for services to start..."
    sleep 10
    
    if ! check_services; then
        echo "Failed to start services!"
        docker-compose -f docker-compose-cobol.yml logs
        return 1
    fi
}

# Monitor command output
monitor_commands() {
    echo
    echo "Monitoring command execution..."
    
    # Start monitoring in background
    (
        while true; do
            echo "STATUS" | nc localhost 9999 2>/dev/null || true
            sleep 2
        done
    ) &
    MONITOR_PID=$!
}

# Cleanup
cleanup() {
    [ -n "$MONITOR_PID" ] && kill $MONITOR_PID 2>/dev/null || true
    rm -f /tmp/doom_state.dat
}
trap cleanup EXIT

# Main test
main() {
    # Start services if not running
    if ! check_services; then
        start_services || exit 1
    fi
    
    echo
    echo "======================================"
    echo "Test 1: Low Health Response"
    echo "======================================"
    
    # Create state with low health
    create_test_state 25
    
    echo "Waiting for COBOL processing..."
    sleep 5
    
    echo
    echo "Expected: MOVE BACK, TURN LEFT (retreat)"
    echo "Checking FTP logs..."
    docker-compose -f docker-compose-cobol.yml logs ftp-gateway | tail -10
    
    echo
    echo "======================================"
    echo "Test 2: High Health Response"
    echo "======================================"
    
    # Create state with high health
    create_test_state 95
    
    echo "Waiting for COBOL processing..."
    sleep 5
    
    echo
    echo "Expected: MOVE FORWARD, TURN RIGHT, SHOOT (explore)"
    echo "Checking FTP logs..."
    docker-compose -f docker-compose-cobol.yml logs ftp-gateway | tail -10
    
    echo
    echo "======================================"
    echo "Test 3: Monitor Complete Loop"
    echo "======================================"
    
    monitor_commands
    
    # Run several cycles
    for i in {1..3}; do
        echo
        echo "Cycle $i:"
        health=$((100 - i * 20))
        create_test_state $health
        sleep 3
        
        echo "Bridge logs:"
        docker-compose -f docker-compose-cobol.yml logs --tail=5 doom-bridge
    done
    
    echo
    echo "======================================"
    echo "Test Complete!"
    echo "======================================"
    
    # Show final logs
    echo
    echo "Final service status:"
    docker-compose -f docker-compose-cobol.yml ps
    
    echo
    echo "To view full logs:"
    echo "  docker-compose -f docker-compose-cobol.yml logs"
}

# Run main
main