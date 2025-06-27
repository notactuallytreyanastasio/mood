#!/usr/bin/env python3
"""Test different keyboard input methods for DOOM on macOS"""

import pyautogui
import time
import subprocess
import sys

print("DOOM Keyboard Input Test - macOS")
print("=" * 50)

print("\n⚠️  IMPORTANT: Click on the DOOM window to focus it!")
input("Press Enter when DOOM is focused...")

print("\nTesting different keyboard methods...")
print("-" * 40)

# Method 1: Standard press
print("\nMethod 1: pyautogui.press('escape')")
pyautogui.press('escape')
time.sleep(1)

# Method 2: keyDown/keyUp with longer delay
print("Method 2: keyDown/keyUp with delay")
pyautogui.keyDown('escape')
time.sleep(0.2)
pyautogui.keyUp('escape')
time.sleep(1)

# Method 3: Write/typewrite
print("Method 3: pyautogui.write()")
pyautogui.write(' ', interval=0.1)  # Space key
time.sleep(1)

# Method 4: Hotkey
print("Method 4: pyautogui.hotkey()")
pyautogui.hotkey('enter')
time.sleep(1)

# Method 5: Using AppleScript (macOS specific)
print("Method 5: AppleScript key events")
try:
    applescript = '''
    tell application "System Events"
        key code 53
    end tell
    '''
    subprocess.run(['osascript', '-e', applescript], check=True)
    time.sleep(1)
except Exception as e:
    print(f"  AppleScript failed: {e}")

# Method 6: Multiple rapid presses
print("Method 6: Multiple rapid presses")
for _ in range(3):
    pyautogui.press('escape')
    time.sleep(0.1)

print("\n" + "=" * 50)
print("Which method(s) worked with DOOM?")
print("If none worked, we may need to:")
print("1. Use a different approach (like Karabiner-Elements)")
print("2. Check if DOOM needs specific window activation")
print("3. Try running DOOM with different settings")