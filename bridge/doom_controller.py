#!/usr/bin/env python3
"""
DOOM Controller Module
Sends keyboard/mouse input to DOOM
"""

import logging
import pyautogui
from typing import Optional

# Platform detection
try:
    from Xlib import display as x_display
    PLATFORM = 'linux'
except ImportError:
    PLATFORM = 'other'


class DoomController:
    """Send keyboard/mouse input to DOOM"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.doom_window = None
        
        # Configure pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.1
        
    def execute_command(self, cmd):
        """Execute a command from COBOL"""
        self.logger.debug(f"Executing: {cmd}")
        
        try:
            if cmd.cmd_type == 'K':
                # Keyboard command
                key = cmd.code.strip().lower()
                if cmd.action == 'P':
                    pyautogui.keyDown(key)
                else:
                    pyautogui.keyUp(key)
                    
            elif cmd.cmd_type == 'M':
                # Mouse command
                if cmd.code.strip() == 'MOVE':
                    pyautogui.moveRel(cmd.mouse_dx, cmd.mouse_dy)
                elif cmd.action == 'P':
                    pyautogui.mouseDown()
                else:
                    pyautogui.mouseUp()
                    
        except Exception as e:
            self.logger.error(f"Failed to execute command: {e}")