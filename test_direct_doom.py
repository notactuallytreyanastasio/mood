#!/usr/bin/env python3
"""Test script for direct_doom.py fixes"""

import sys
import time
import subprocess

# Add cobol-interface to path
sys.path.insert(0, 'cobol-interface')

from direct_doom import doom_controller, PYAUTOGUI_AVAILABLE

def test_doom_control():
    """Test the fixed direct_doom.py controller"""
    
    print("DOOM Direct Control Test")
    print("=" * 50)
    
    # Check if pyautogui is available
    if not PYAUTOGUI_AVAILABLE:
        print("❌ ERROR: pyautogui is not available!")
        print("Run: pip3 install pyautogui")
        return False
        
    print("✓ pyautogui is available")
    
    # Check display
    import os
    if 'DISPLAY' in os.environ:
        print(f"✓ Display is set to: {os.environ['DISPLAY']}")
    else:
        print("⚠️  Display not set, using default :99")
    
    print("\n⚠️  IMPORTANT: Make sure DOOM is running in windowed mode!")
    print("Run in another terminal: chocolate-doom -iwad wads/doom1.wad -window")
    
    input("\nPress Enter when DOOM is running and focused...")
    
    print("\nTesting movement commands...")
    print("-" * 30)
    
    # Test each movement direction
    movements = [
        ("FORWARD", 0.5, "Moving forward for 0.5 seconds"),
        ("BACK", 0.5, "Moving backward for 0.5 seconds"),
        ("LEFT", 0.5, "Strafing left for 0.5 seconds"),
        ("RIGHT", 0.5, "Strafing right for 0.5 seconds")
    ]
    
    for direction, duration, description in movements:
        print(f"\n{description}...")
        doom_controller.add_move_command(direction, duration)
        time.sleep(duration + 0.5)  # Wait for command to complete
        
    print("\nTesting turn commands...")
    print("-" * 30)
    
    # Test turning
    turns = [
        ("LEFT", 45, "Turning left 45 degrees"),
        ("RIGHT", 90, "Turning right 90 degrees"),
        ("LEFT", 45, "Turning left 45 degrees (back to center)")
    ]
    
    for direction, degrees, description in turns:
        print(f"\n{description}...")
        doom_controller.add_turn_command(direction, degrees)
        time.sleep(0.5)
        
    print("\nTesting action commands...")
    print("-" * 30)
    
    # Test shooting
    print("\nShooting 3 times...")
    doom_controller.add_shoot_command(3)
    time.sleep(1)
    
    # Test use key
    print("\nPressing USE key (for doors/switches)...")
    doom_controller.add_use_command()
    time.sleep(0.5)
    
    # Test weapon switching
    print("\nSwitching to weapon 2...")
    doom_controller.add_weapon_command(2)
    time.sleep(0.5)
    
    print("\n" + "=" * 50)
    print("✓ Test completed!")
    print("\nIf DOOM responded to all commands, direct_doom.py is working correctly!")
    
    return True

if __name__ == "__main__":
    test_doom_control()