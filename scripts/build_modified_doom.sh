#!/bin/bash
# Build DOOM with state export and network input functionality

set -e  # Exit on error

echo "================================"
echo "Building Modified DOOM"
echo "================================"

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v gcc &> /dev/null; then
    echo "❌ Error: gcc not found. Please install build tools."
    exit 1
fi

if [ ! -d "linuxdoom-1.10" ]; then
    echo "❌ Error: DOOM source not found in linuxdoom-1.10/"
    echo "Please ensure you have the Linux DOOM 1.10 source code."
    exit 1
fi

# Create backup of original source
if [ ! -d "linuxdoom-1.10.orig" ]; then
    echo "Creating backup of original source..."
    cp -r linuxdoom-1.10 linuxdoom-1.10.orig
fi

# Apply patches
echo
echo "Applying patches..."

# Check if patches already applied
if grep -q "x_state.h" linuxdoom-1.10/g_game.c 2>/dev/null; then
    echo "✓ State export patch already applied"
else
    echo "Applying state export patch..."
    patch -p0 < doom-state-export.patch || {
        echo "❌ Failed to apply state export patch"
        exit 1
    }
fi

if grep -q "n_input.h" linuxdoom-1.10/d_main.c 2>/dev/null; then
    echo "✓ Network input patch already applied"  
else
    echo "Applying network input patch..."
    patch -p0 < doom-network-input.patch || {
        echo "❌ Failed to apply network input patch"
        exit 1
    }
fi

# Enter source directory
cd linuxdoom-1.10

# Clean previous build
echo
echo "Cleaning previous build..."
make clean 2>/dev/null || true

# Build DOOM
echo
echo "Building DOOM..."
echo "This may take a minute..."

make || {
    echo
    echo "❌ Build failed!"
    echo "Common issues:"
    echo "- Missing X11 dev libraries: sudo apt-get install libx11-dev"
    echo "- Old compiler: Need GCC with C99 support"
    exit 1
}

# Check if build succeeded
if [ -f "linux/linuxxdoom" ]; then
    echo
    echo "✅ Build successful!"
    echo
    echo "Modified DOOM features:"
    echo "- State export on UDP port 31337"
    echo "- Network input on UDP port 31338"
    echo "- COBOL format output to /tmp/doom_state.dat"
    echo
    echo "To run:"
    echo "  cd linuxdoom-1.10/linux"
    echo "  ./linuxxdoom -iwad ../../wads/doom1.wad"
    echo
    echo "To disable features:"
    echo "  -noexport    Disable state export"
    echo "  -nonetinput  Disable network input"
else
    echo "❌ Build failed - executable not found"
    exit 1
fi