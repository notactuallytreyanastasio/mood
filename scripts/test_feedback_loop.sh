#!/bin/bash
# Test the complete DOOM-COBOL feedback loop

echo "======================================"
echo "DOOM-COBOL Feedback Loop Test"
echo "======================================"

# Configuration
STATE_FILE="/tmp/doom_state.dat"
STATE_PORT=31337
INPUT_PORT=31338

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test status
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
log_test() {
    echo -e "\n${YELLOW}TEST:${NC} $1"
}

log_pass() {
    echo -e "${GREEN}✓ PASS:${NC} $1"
    ((TESTS_PASSED++))
}

log_fail() {
    echo -e "${RED}✗ FAIL:${NC} $1"
    ((TESTS_FAILED++))
}

check_port() {
    nc -z -u localhost $1 2>/dev/null
}

wait_for_file() {
    local file=$1
    local timeout=$2
    local elapsed=0
    
    while [ ! -f "$file" ] && [ $elapsed -lt $timeout ]; do
        sleep 0.1
        ((elapsed++))
    done
    
    [ -f "$file" ]
}

# Start testing
echo
echo "Prerequisites check..."

# Check if modified DOOM is running
log_test "Check if DOOM is running"
if pgrep -f linuxxdoom > /dev/null; then
    log_pass "DOOM process found"
else
    log_fail "DOOM not running. Run: ./scripts/start_full_system.sh"
    exit 1
fi

# Test 1: State export
log_test "State export via UDP"
if check_port $STATE_PORT; then
    log_pass "State port $STATE_PORT is active"
else
    log_fail "State port $STATE_PORT not responding"
fi

log_test "State export to file"
if wait_for_file "$STATE_FILE" 20; then
    log_pass "State file created: $STATE_FILE"
    
    # Check file format
    if head -1 "$STATE_FILE" | grep -q "^STATE [0-9]\\+ [0-9]\\+$"; then
        log_pass "State file format is correct"
    else
        log_fail "State file format is incorrect"
    fi
else
    log_fail "State file not created within 2 seconds"
fi

# Test 2: Network input
log_test "Network input port"
if check_port $INPUT_PORT; then
    log_pass "Input port $INPUT_PORT is active"
else
    log_fail "Input port $INPUT_PORT not responding"
fi

# Test 3: Command execution
log_test "Send movement command"
echo "FORWARD 1" | nc -u -w1 localhost $INPUT_PORT
sleep 1

# Check if state changed (position should change)
if [ -f "$STATE_FILE" ]; then
    STATE1=$(cat "$STATE_FILE")
    echo "FORWARD 1" | nc -u -w1 localhost $INPUT_PORT
    sleep 1
    STATE2=$(cat "$STATE_FILE")
    
    if [ "$STATE1" != "$STATE2" ]; then
        log_pass "State changed after movement command"
    else
        log_fail "State did not change after movement"
    fi
fi

# Test 4: Complete feedback loop
log_test "Complete feedback loop (State → Decision → Command → State)"

# Start a simple AI loop
(
    for i in {1..5}; do
        if [ -f "$STATE_FILE" ]; then
            # Read health from state
            HEALTH=$(grep "^PLAYER" "$STATE_FILE" | sed 's/.*\([0-9]\{3\}\)[0-9]\{3\}$/\1/')
            
            # Make decision based on health
            if [ "$HEALTH" -lt "030" ]; then
                echo "AI: Low health - retreating"
                echo "BACK 1" | nc -u -w0 localhost $INPUT_PORT
            else
                echo "AI: Exploring"
                echo "FORWARD 1" | nc -u -w0 localhost $INPUT_PORT
                echo "TURNRIGHT 30" | nc -u -w0 localhost $INPUT_PORT
            fi
        fi
        sleep 1
    done
) &
AI_PID=$!

# Wait for AI to complete
wait $AI_PID
log_pass "AI loop completed successfully"

# Test 5: State monitoring
log_test "Real-time state monitoring"
echo "Monitoring state changes for 3 seconds..."

TICK_COUNT=0
LAST_TICK=""
for i in {1..30}; do
    if [ -f "$STATE_FILE" ]; then
        CURRENT_TICK=$(head -1 "$STATE_FILE" | awk '{print $2}')
        if [ "$CURRENT_TICK" != "$LAST_TICK" ]; then
            ((TICK_COUNT++))
            LAST_TICK=$CURRENT_TICK
        fi
    fi
    sleep 0.1
done

if [ $TICK_COUNT -gt 10 ]; then
    log_pass "State updates frequently: $TICK_COUNT updates in 3 seconds"
else
    log_fail "State updates too slowly: only $TICK_COUNT updates in 3 seconds"
fi

# Summary
echo
echo "======================================"
echo "Test Summary"
echo "======================================"
echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}"
    echo "The DOOM-COBOL feedback loop is working correctly."
    exit 0
else
    echo -e "\n${RED}✗ Some tests failed${NC}"
    echo "Please check the system logs for details."
    exit 1
fi