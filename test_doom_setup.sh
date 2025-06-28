#!/bin/bash
# Test DOOM setup

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Testing DOOM Setup${NC}"
echo "==================="
echo

# Check if DOOM source exists
if [ -d "linuxdoom-1.10" ]; then
    echo -e "${GREEN}✓ DOOM source found${NC}"
else
    echo -e "${RED}✗ DOOM source not found${NC}"
    exit 1
fi

# Check patches
if [ -f "doom-state-export.patch" ] && [ -f "doom-network-input.patch" ]; then
    echo -e "${GREEN}✓ Patches found${NC}"
else
    echo -e "${RED}✗ Patches missing${NC}"
    exit 1
fi

# Run setup
echo
echo "Running DOOM setup..."
cd build_system
./setup_doom.sh

echo
echo -e "${GREEN}Setup complete!${NC}"

# Check result
if [ -f "doom_install/doom_path.txt" ]; then
    DOOM_PATH=$(cat doom_install/doom_path.txt)
    echo "DOOM executable: $DOOM_PATH"
    
    if [ -f "$DOOM_PATH" ]; then
        echo -e "${GREEN}✓ DOOM built successfully${NC}"
        
        # Check for modifications
        if strings "$DOOM_PATH" | grep -q "X_ExportState"; then
            echo -e "${GREEN}✓ State export patch applied${NC}"
        fi
        
        if strings "$DOOM_PATH" | grep -q "N_InitNetworkInput"; then
            echo -e "${GREEN}✓ Network input patch applied${NC}"
        fi
    else
        echo -e "${RED}✗ DOOM executable not found${NC}"
    fi
else
    echo -e "${RED}✗ Build failed${NC}"
fi