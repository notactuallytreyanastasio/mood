#!/bin/bash
# Startup script for Hercules MVS

echo "Starting Hercules MVS for DOOM-COBOL..."

# Check if TK4- is properly extracted
if [ ! -f "conf/tk4-.cnf" ]; then
    echo "ERROR: TK4- not found. The Docker build should have downloaded it."
    exit 1
fi

# Create DOOM DASD if it doesn't exist
if [ ! -f "dasd/doomd1.3350" ]; then
    echo "Creating DOOM DASD volume..."
    dasdinit -z dasd/doomd1.3350 3350 DOOM01 1000
fi

# Start Hercules with TK4- configuration
# We'll use the standard TK4- config and add our customizations
echo "Starting Hercules..."
hercules -f conf/tk4-.cnf -d

# Note: TK4- automatically starts MVS
# After startup:
# - Port 3270: TN3270 terminals
# - Port 8038: HTTP console
# - Port 3505: Card reader (JCL submission)