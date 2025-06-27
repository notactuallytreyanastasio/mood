#!/bin/bash
# Start Xvfb in the background
Xvfb :99 -screen 0 1024x768x24 &
XVFB_PID=$!

# Wait for Xvfb to start
sleep 2

# Set display
export DISPLAY=:99

# Create a dummy .Xauthority file
touch /root/.Xauthority

# Start the COBOL interface
python -u cobol_interface.py

# If it exits, kill Xvfb
kill $XVFB_PID