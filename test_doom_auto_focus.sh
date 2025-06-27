#!/bin/bash
# Auto-focus DOOM after starting test

echo "Starting DOOM test with auto-focus..."
echo "Make sure DOOM is already running!"

# Start the test in background
python3 test_doom_delayed.py &

# Wait a moment
sleep 2

# Try to focus DOOM window
osascript -e 'tell application "chocolate-doom" to activate' 2>/dev/null || \
osascript -e 'tell application "System Events" to tell process "chocolate-doom" to set frontmost to true' 2>/dev/null

echo "Test running..."
wait