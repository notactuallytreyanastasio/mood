#!/usr/bin/env python3
"""Test AppleScript DOOM control"""

import sys
sys.path.insert(0, 'cobol-interface')

from applescript_doom import doom_controller
import time

print("AppleScript DOOM Control Test")
print("=" * 50)

print("\n⚠️  IMPORTANT: Click on the DOOM window to focus it!")
input("Press Enter when DOOM is focused...")

print("\nTest 1: ESC key (menu/pause)")
doom_controller.add_escape_command()
time.sleep(2)

print("Test 2: Enter key")
doom_controller.add_enter_command()
time.sleep(2)

print("Test 3: Movement (W for 1 second)")
doom_controller.add_move_command('FORWARD', 1.0)
time.sleep(2)

print("Test 4: Turn right")
doom_controller.add_turn_command('RIGHT', 45)
time.sleep(1)

print("Test 5: Shoot")
doom_controller.add_shoot_command(2)
time.sleep(2)

print("\n✓ Tests complete!")
print("If this worked better than pyautogui, the COBOL interface will now use AppleScript!")