#!/usr/bin/env python3
"""Debug version of COBOL interface with verbose logging"""

import sys
sys.path.insert(0, 'cobol-interface')

# Patch logging before importing
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Now import the interface
from cobol_interface import COBOLInterface
import pyautogui

print("Debug COBOL Interface")
print("=" * 50)

# Check pyautogui
try:
    print(f"✓ pyautogui available: {pyautogui.size()}")
    print(f"✓ Mouse position: {pyautogui.position()}")
except Exception as e:
    print(f"❌ pyautogui error: {e}")

# Check direct_doom import
try:
    from direct_doom import doom_controller, PYAUTOGUI_AVAILABLE
    print(f"✓ direct_doom imported, pyautogui available: {PYAUTOGUI_AVAILABLE}")
    print(f"✓ doom_controller initialized: {doom_controller.running}")
except Exception as e:
    print(f"❌ direct_doom error: {e}")

print("\nStarting COBOL interface on port 9999...")
print("Test with: echo 'ESC' | nc localhost 9999")

try:
    interface = COBOLInterface()
    interface.start()
except KeyboardInterrupt:
    print("\nShutdown requested")
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()