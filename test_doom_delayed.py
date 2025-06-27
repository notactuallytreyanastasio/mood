#!/usr/bin/env python3
"""Test DOOM control with auto-delay for window focusing"""

import sys
sys.path.insert(0, 'cobol-interface')
import time

print("DOOM Control Test with Delay")
print("=" * 50)
print("\nYou have 5 seconds to click on the DOOM window!")
print("Starting countdown...")

for i in range(5, 0, -1):
    print(f"{i}...")
    time.sleep(1)

print("\nRunning tests!")

# Test with AppleScript method
try:
    from applescript_doom import doom_controller
    print("Using AppleScript controller")
except:
    from direct_doom import doom_controller
    print("Using pyautogui controller")

print("\nTest 1: ESC key")
doom_controller.add_escape_command()
time.sleep(1)

print("Test 2: Enter key")
doom_controller.add_enter_command()
time.sleep(1)

print("Test 3: Forward movement")
doom_controller.add_move_command('FORWARD', 1.0)
time.sleep(2)

print("\n✓ Tests complete! Check if DOOM responded.")