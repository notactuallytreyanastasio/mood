#!/bin/bash
# Fix DOOM control on macOS

echo "=== Fixing DOOM Control Setup ==="
echo ""

# 1. Stop Docker containers
echo "1. Stopping Docker containers..."
docker-compose -f docker-compose-simple.yml down 2>/dev/null || true

# 2. Check Python and install dependencies
echo ""
echo "2. Installing Python dependencies..."
pip3 install pyautogui pyobjc-core pyobjc flask flask-cors

# 3. Important macOS permissions
echo ""
echo "3. IMPORTANT: macOS Accessibility Permissions"
echo "   ----------------------------------------"
echo "   pyautogui needs accessibility permissions to control the mouse/keyboard."
echo "   "
echo "   Please do the following:"
echo "   1. Open System Preferences > Security & Privacy > Privacy > Accessibility"
echo "   2. Click the lock to make changes"
echo "   3. Add Terminal.app (or iTerm.app) to the allowed apps"
echo "   4. Make sure it's checked/enabled"
echo ""
read -p "Press Enter after you've granted accessibility permissions..."

# 4. Test pyautogui
echo ""
echo "4. Testing pyautogui..."
python3 -c "
import pyautogui
print('Screen size:', pyautogui.size())
print('Mouse position:', pyautogui.position())
print('pyautogui is working!')
" || echo "ERROR: pyautogui test failed"

# 5. Create simple test script
echo ""
echo "5. Creating test script..."
cat > test_doom_control.py << 'EOF'
#!/usr/bin/env python3
import time
import pyautogui

print("DOOM Control Test")
print("=================")
print("Make sure DOOM is running in windowed mode!")
print("")
print("This will:")
print("1. Wait 3 seconds for you to focus on DOOM")
print("2. Move forward for 1 second")
print("3. Turn right")
print("4. Shoot once")
print("")
input("Press Enter to start test...")

print("Focus on DOOM window now! Starting in 3...")
time.sleep(1)
print("2...")
time.sleep(1)
print("1...")
time.sleep(1)

print("Moving forward...")
pyautogui.keyDown('w')
time.sleep(1)
pyautogui.keyUp('w')

print("Turning right...")
pyautogui.moveRel(100, 0)

print("Shooting...")
pyautogui.click()

print("Test complete!")
EOF

chmod +x test_doom_control.py

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To run the system:"
echo "1. Start DOOM in windowed mode: chocolate-doom -window"
echo "2. Run the local COBOL interface: ./run_local_cobol.sh"
echo "3. Send commands: echo 'MOVE FORWARD 2' | nc localhost 9999"
echo ""
echo "Or test directly: python3 test_doom_control.py"