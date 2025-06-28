#!/bin/bash
# Quick test without Docker

echo "Quick DOOM-COBOL Test"
echo "===================="

# Test 1: Check Python modules
echo
echo "1. Checking Python modules..."
python3 -c "import pyftpdlib; print('✓ pyftpdlib available')" 2>/dev/null || echo "✗ pyftpdlib missing - run: pip3 install pyftpdlib"
python3 -c "import structlog; print('✓ structlog available')" 2>/dev/null || echo "✗ structlog missing - run: pip3 install structlog"

# Test 2: Test FTP server
echo
echo "2. Testing FTP server..."
cd ftp-gateway
python3 -c "
from mock_ftp_server import MVSDatasetHandler
print('✓ FTP server can be imported')
" || echo "✗ FTP server has errors"
cd ..

# Test 3: Test COBOL interface
echo
echo "3. Testing COBOL interface..."
cd cobol-interface
python3 -c "
from cobol_interface import COBOLInterface
print('✓ COBOL interface can be imported')
" || echo "✗ COBOL interface has errors"
cd ..

# Test 4: Create test state
echo
echo "4. Creating test state file..."
cat > /tmp/doom_state.dat << EOF
STATE 00001234 01
PLAYER+0001024+0001024+0000000+090075050
AMMO  0050002001000040 2
EOF
echo "✓ Created /tmp/doom_state.dat"
cat /tmp/doom_state.dat

echo
echo "===================="
echo "Ready to run full test with: ./test_simple_loop.sh"