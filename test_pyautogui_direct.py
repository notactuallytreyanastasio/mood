#!/usr/bin/env python3
"""Direct test of pyautogui with DOOM - no COBOL interface"""

import pyautogui
import time
import sys

print("Direct pyautogui DOOM Test")
print("=" * 50)

# Check if pyautogui is working
try:
    print("Testing pyautogui...")
    print(f"Screen size: {pyautogui.size()}")
    print(f"Mouse position: {pyautogui.position()}")
    print("✓ pyautogui is working")
except Exception as e:
    print(f"❌ pyautogui error: {e}")
    sys.exit(1)

print("\n⚠️  Make sure:")
print("1. DOOM is running in windowed mode")
print("2. DOOM window is focused (click on it)")
print("3. You're not in fullscreen mode")

input("\nPress Enter when ready...")

print("\nTest 1: ESC key (should skip demo or pause)")
pyautogui.press('escape')
time.sleep(1)

print("Test 2: Enter key (select menu option)")
pyautogui.press('enter')
time.sleep(1)

print("Test 3: Movement test (W key for 1 second)")
pyautogui.keyDown('w')
time.sleep(1)
pyautogui.keyUp('w')
time.sleep(0.5)

print("Test 4: Mouse movement (turn right)")
pyautogui.moveRel(100, 0, duration=0.5)
time.sleep(0.5)

print("Test 5: Mouse click (shoot)")
pyautogui.click()
time.sleep(0.5)

print("\n✓ Tests complete!")
print("\nIf DOOM didn't respond:")
print("1. Check Terminal has accessibility permissions")
print("2. Make sure DOOM window was focused")
print("3. Try running with sudo (not recommended)")
print("4. Check if any security software is blocking input")