#!/bin/bash
# DOOM Launcher for COBOL Control
# This script launches DOOM in a way that's easy for our system to control

DOOM_EXECUTABLE=""
DOOM_IWAD=""

# Try to find DOOM executable
if command -v chocolate-doom &> /dev/null; then
    DOOM_EXECUTABLE="chocolate-doom"
elif command -v doom &> /dev/null; then
    DOOM_EXECUTABLE="doom"
elif command -v gzdoom &> /dev/null; then
    DOOM_EXECUTABLE="gzdoom"
elif [ -f "./doom" ]; then
    DOOM_EXECUTABLE="./doom"
fi

if [ -z "$DOOM_EXECUTABLE" ]; then
    echo "ERROR: No DOOM executable found!"
    echo "Please install chocolate-doom, gzdoom, or provide doom executable"
    exit 1
fi

# Try to find DOOM IWAD
IWAD_PATHS=(
    "$HOME/.local/share/games/doom/doom1.wad"
    "$HOME/.local/share/games/doom/doom.wad"
    "/usr/share/games/doom/doom1.wad"
    "/usr/share/games/doom/doom.wad"
    "./doom1.wad"
    "./doom.wad"
    "./DOOM1.WAD"
    "./DOOM.WAD"
)

for iwad in "${IWAD_PATHS[@]}"; do
    if [ -f "$iwad" ]; then
        DOOM_IWAD="$iwad"
        break
    fi
done

if [ -z "$DOOM_IWAD" ] && [ "$1" != "--no-iwad" ]; then
    echo "WARNING: No DOOM IWAD found. DOOM may not start correctly."
    echo "Looking for doom1.wad or doom.wad in common locations..."
fi

echo "Starting DOOM for COBOL control..."
echo "Executable: $DOOM_EXECUTABLE"
[ -n "$DOOM_IWAD" ] && echo "IWAD: $DOOM_IWAD"

# Launch DOOM with specific settings for automation
case "$DOOM_EXECUTABLE" in
    chocolate-doom)
        # Chocolate Doom settings
        $DOOM_EXECUTABLE \
            ${DOOM_IWAD:+-iwad "$DOOM_IWAD"} \
            -window \
            -geometry 640x480 \
            -nosound \
            -nomusic \
            -skill 2 \
            -warp 1 1 \
            &
        ;;
    gzdoom)
        # GZDoom settings
        $DOOM_EXECUTABLE \
            ${DOOM_IWAD:+-iwad "$DOOM_IWAD"} \
            +vid_forcesurface 1 \
            +fullscreen 0 \
            +vid_defwidth 640 \
            +vid_defheight 480 \
            +snd_output "null" \
            +skill 2 \
            +map E1M1 \
            &
        ;;
    *)
        # Generic DOOM
        $DOOM_EXECUTABLE \
            ${DOOM_IWAD:+-iwad "$DOOM_IWAD"} \
            -window \
            -skill 2 \
            &
        ;;
esac

DOOM_PID=$!
echo "DOOM started with PID: $DOOM_PID"
echo "Saving PID to /tmp/doom-cobol.pid"
echo $DOOM_PID > /tmp/doom-cobol.pid

# Wait a moment for DOOM to initialize
sleep 3

echo "DOOM should now be running and ready for COBOL control!"
echo "Window title should contain 'DOOM' for the bridge to find it."
echo ""
echo "To send commands:"
echo "  echo 'MOVE FORWARD' | nc localhost 9999"
echo "  echo 'TURN RIGHT 45' | nc localhost 9999"
echo "  echo 'SHOOT' | nc localhost 9999"
echo ""
echo "Press Ctrl+C to stop monitoring (DOOM will keep running)"

# Keep script running to monitor
wait $DOOM_PID