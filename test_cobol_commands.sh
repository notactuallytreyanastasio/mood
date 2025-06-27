#!/bin/bash
# Test COBOL interface commands

echo "DOOM COBOL Interface Test"
echo "========================="
echo
echo "This script tests the COBOL interface by sending commands to port 9999"
echo "Make sure:"
echo "1. DOOM is running in windowed mode (chocolate-doom -iwad wads/doom1.wad -window)"
echo "2. COBOL interface is running (./run_local_cobol.sh)"
echo
echo "Press Enter to start test..."
read

echo
echo "Testing movement commands..."
echo "---------------------------"

echo "Moving forward for 2 seconds..."
echo "MOVE FORWARD 2" | nc localhost 9999
sleep 3

echo "Moving backward for 1 second..."
echo "MOVE BACK 1" | nc localhost 9999
sleep 2

echo "Strafing left for 1 second..."
echo "MOVE LEFT 1" | nc localhost 9999
sleep 2

echo "Strafing right for 1 second..."
echo "MOVE RIGHT 1" | nc localhost 9999
sleep 2

echo
echo "Testing turn commands..."
echo "------------------------"

echo "Turning left 45 degrees..."
echo "TURN LEFT 45" | nc localhost 9999
sleep 1

echo "Turning right 90 degrees..."
echo "TURN RIGHT 90" | nc localhost 9999
sleep 1

echo "Turning left 45 degrees (centering)..."
echo "TURN LEFT 45" | nc localhost 9999
sleep 1

echo
echo "Testing action commands..."
echo "--------------------------"

echo "Shooting 3 times..."
echo "SHOOT 3" | nc localhost 9999
sleep 2

echo "Using door/switch..."
echo "USE" | nc localhost 9999
sleep 1

echo "Switching to weapon 2..."
echo "WEAPON 2" | nc localhost 9999
sleep 1

echo
echo "Testing menu navigation..."
echo "--------------------------"

echo "Pressing ESC..."
echo "ESC" | nc localhost 9999
sleep 1

echo "Pressing Enter..."
echo "ENTER" | nc localhost 9999
sleep 1

echo
echo "Testing status command..."
echo "-------------------------"
echo "STATUS" | nc localhost 9999

echo
echo "========================="
echo "Test completed!"
echo
echo "If DOOM responded to all commands, the system is working correctly!"