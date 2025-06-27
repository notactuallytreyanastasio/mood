#!/bin/bash
# Run COBOL interface locally to control DOOM on macOS

echo "Setting up local COBOL-DOOM interface..."

# Check if we're in the right directory
if [ ! -f "cobol-interface/cobol_interface.py" ]; then
    echo "Error: Must run from DOOM project root directory"
    exit 1
fi

# Install Python dependencies locally
echo "Installing Python dependencies..."
pip3 install pyautogui flask flask-cors websockets aiohttp

# Stop any existing Docker containers
echo "Stopping Docker containers..."
docker-compose -f docker-compose-simple.yml down 2>/dev/null || true

# Start the COBOL interface locally
echo "Starting COBOL interface on port 9999..."
echo "Make sure DOOM is running in windowed mode!"
echo ""
echo "Example commands:"
echo "  echo 'MOVE FORWARD 2' | nc localhost 9999"
echo "  echo 'TURN RIGHT 90' | nc localhost 9999"
echo "  echo 'SHOOT 3' | nc localhost 9999"
echo ""

cd cobol-interface
python3 cobol_interface.py