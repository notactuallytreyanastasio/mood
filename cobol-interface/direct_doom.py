#!/usr/bin/env python3
"""
Direct DOOM controller for the COBOL interface
Executes commands directly without bridge service
"""

import time
import threading
from typing import List
import logging
import sys
import platform

# Check if we're on macOS
IS_MACOS = platform.system() == 'Darwin'

# Try to import the appropriate controller
CONTROLLER_AVAILABLE = False
doom_controller = None

if IS_MACOS:
    # On macOS, prefer AppleScript controller
    try:
        from applescript_doom import doom_controller
        CONTROLLER_AVAILABLE = True
        logging.info("Using AppleScript controller for macOS")
    except ImportError as e:
        logging.warning(f"AppleScript controller not available: {e}")
        
# Fallback to pyautogui
if not CONTROLLER_AVAILABLE:
    try:
        import os
        # Set a dummy display if not set
        if 'DISPLAY' not in os.environ:
            os.environ['DISPLAY'] = ':99'
        import pyautogui
        PYAUTOGUI_AVAILABLE = True
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.1
    except ImportError as e:
        PYAUTOGUI_AVAILABLE = False
        logging.warning(f"pyautogui not available - DOOM control disabled: {e}")

class DirectDoomController:
    """Execute DOOM commands directly"""
    
    def __init__(self):
        self.command_queue = []
        self.running = True
        if PYAUTOGUI_AVAILABLE:
            self.start_executor()
        
    def start_executor(self):
        """Start background command executor"""
        self.executor_thread = threading.Thread(target=self._execute_loop, daemon=True)
        self.executor_thread.start()
        
    def _execute_loop(self):
        """Background loop to execute commands"""
        while self.running:
            if self.command_queue:
                cmd = self.command_queue.pop(0)
                self._execute_command(cmd)
            time.sleep(0.05)  # 20 Hz
            
    def _execute_command(self, cmd: dict):
        """Execute a single command"""
        if not PYAUTOGUI_AVAILABLE:
            return
            
        try:
            if cmd['type'] == 'key':
                if cmd['action'] == 'press':
                    pyautogui.keyDown(cmd['key'])
                elif cmd['action'] == 'keyUp':
                    pyautogui.keyUp(cmd['key'])
                    
            elif cmd['type'] == 'mouse':
                if cmd['action'] == 'move':
                    pyautogui.moveRel(cmd['dx'], cmd['dy'])
                elif cmd['action'] == 'click':
                    pyautogui.click()
                    
            elif cmd['type'] == 'wait':
                time.sleep(cmd['duration'] / 1000.0)  # Convert ms to seconds
                
        except Exception as e:
            logging.error(f"Failed to execute command: {e}")
            
    def add_move_command(self, direction: str, duration: float):
        """Add movement command to queue"""
        key_map = {
            'FORWARD': 'w',
            'BACK': 's', 
            'LEFT': 'a',
            'RIGHT': 'd'
        }
        
        if direction in key_map:
            self.command_queue.extend([
                {'type': 'key', 'action': 'press', 'key': key_map[direction]},
                {'type': 'wait', 'duration': int(duration * 1000)},
                {'type': 'key', 'action': 'keyUp', 'key': key_map[direction]}
            ])
            
    def add_turn_command(self, direction: str, degrees: int):
        """Add turn command to queue"""
        pixels = degrees * 5  # Adjust sensitivity as needed
        dx = pixels if direction == 'RIGHT' else -pixels
        
        self.command_queue.append({
            'type': 'mouse', 'action': 'move', 'dx': dx, 'dy': 0
        })
        
    def add_shoot_command(self, count: int):
        """Add shoot command to queue"""
        for _ in range(count):
            self.command_queue.extend([
                {'type': 'mouse', 'action': 'click'},
                {'type': 'wait', 'duration': 100}
            ])
            
    def add_use_command(self):
        """Add use command to queue"""
        self.command_queue.extend([
            {'type': 'key', 'action': 'press', 'key': 'e'},
            {'type': 'wait', 'duration': 100},
            {'type': 'key', 'action': 'keyUp', 'key': 'e'}
        ])
        
    def add_weapon_command(self, weapon_num: int):
        """Add weapon switch command to queue"""
        self.command_queue.extend([
            {'type': 'key', 'action': 'press', 'key': str(weapon_num)},
            {'type': 'wait', 'duration': 50},
            {'type': 'key', 'action': 'keyUp', 'key': str(weapon_num)}
        ])
        
    def add_escape_command(self):
        """Add ESC key command to queue"""
        self.command_queue.extend([
            {'type': 'key', 'action': 'press', 'key': 'escape'},
            {'type': 'wait', 'duration': 100},
            {'type': 'key', 'action': 'keyUp', 'key': 'escape'}
        ])
        
    def add_enter_command(self):
        """Add Enter key command to queue"""
        self.command_queue.extend([
            {'type': 'key', 'action': 'press', 'key': 'enter'},
            {'type': 'wait', 'duration': 100},
            {'type': 'key', 'action': 'keyUp', 'key': 'enter'}
        ])

# Global controller instance
if not CONTROLLER_AVAILABLE:
    doom_controller = DirectDoomController()