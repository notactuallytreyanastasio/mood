#!/bin/bash
# Script to navigate DOOM menus and start the game

echo "DOOM Menu Navigation Script"
echo "=========================="
echo
echo "This script sends commands to navigate from DOOM startup to gameplay"
echo "Make sure:"
echo "1. DOOM is running (chocolate-doom -iwad wads/doom1.wad -window)"
echo "2. COBOL interface is running (./run_local_cobol.sh)"
echo
echo "Press Enter to start menu navigation..."
read

echo
echo "Waiting for DOOM to fully load..."
sleep 2

echo "Pressing ESC to skip intro/demo..."
echo "ESC" | nc localhost 9999
sleep 1

echo "Pressing Enter to start new game..."
echo "ENTER" | nc localhost 9999
sleep 1

echo "Selecting Episode 1: Knee-Deep in the Dead..."
echo "ENTER" | nc localhost 9999
sleep 1

echo "Pressing Enter again to select difficulty (default: Hurt Me Plenty)..."
echo "ENTER" | nc localhost 9999
sleep 2

echo "Game should now be loading E1M1..."
echo
echo "You can now send game commands:"
echo "  echo 'MOVE FORWARD 2' | nc localhost 9999"
echo "  echo 'TURN RIGHT 45' | nc localhost 9999"
echo "  echo 'SHOOT 3' | nc localhost 9999"
echo
echo "To pause/unpause: echo 'ESC' | nc localhost 9999"