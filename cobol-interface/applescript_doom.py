#!/usr/bin/env python3
"""
Alternative DOOM controller using AppleScript for macOS
More reliable for game input than pyautogui on macOS
"""

import subprocess
import time
import threading
from typing import List
import logging

class AppleScriptDoomController:
    """Execute DOOM commands using AppleScript"""
    
    # macOS key codes
    KEY_CODES = {
        'w': 13,
        's': 1,
        'a': 0,
        'd': 2,
        'e': 14,
        'escape': 53,
        'enter': 36,
        'return': 36,
        'space': 49,
        '1': 18,
        '2': 19,
        '3': 20,
        '4': 21,
        '5': 23,
        '6': 22,
        '7': 26,
    }
    
    def __init__(self):
        self.command_queue = []
        self.running = True
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
        try:
            if cmd['type'] == 'key':
                self._send_key(cmd['key'], cmd['action'])
            elif cmd['type'] == 'mouse':
                self._send_mouse(cmd)
            elif cmd['type'] == 'wait':
                time.sleep(cmd['duration'] / 1000.0)
        except Exception as e:
            logging.error(f"Failed to execute command: {e}")
            
    def _send_key(self, key: str, action: str):
        """Send keyboard input via AppleScript"""
        if key.lower() in self.KEY_CODES:
            key_code = self.KEY_CODES[key.lower()]
            
            if action == 'press':
                script = f'tell application "System Events" to key code {key_code}'
            elif action == 'keyDown':
                script = f'tell application "System Events" to key down {{key code {key_code}}}'
            elif action == 'keyUp':
                script = f'tell application "System Events" to key up {{key code {key_code}}}'
            else:
                return
                
            subprocess.run(['osascript', '-e', script], capture_output=True)
        else:
            # Try sending as keystroke
            if action == 'press':
                script = f'tell application "System Events" to keystroke "{key}"'
                subprocess.run(['osascript', '-e', script], capture_output=True)
    
    def _send_mouse(self, cmd: dict):
        """Send mouse input via AppleScript"""
        if cmd['action'] == 'move':
            # Get current position
            get_pos = 'tell application "System Events" to get position of mouse'
            result = subprocess.run(['osascript', '-e', get_pos], capture_output=True, text=True)
            if result.stdout:
                try:
                    x, y = map(int, result.stdout.strip().split(', '))
                    new_x = x + cmd['dx']
                    new_y = y + cmd.get('dy', 0)
                    
                    # Move mouse
                    move_script = f'''
                    tell application "System Events"
                        set position of mouse to {{{new_x}, {new_y}}}
                    end tell
                    '''
                    subprocess.run(['osascript', '-e', move_script], capture_output=True)
                except:
                    pass
                    
        elif cmd['action'] == 'click':
            click_script = '''
            tell application "System Events"
                click
            end tell
            '''
            subprocess.run(['osascript', '-e', click_script], capture_output=True)
    
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
                {'type': 'key', 'action': 'keyDown', 'key': key_map[direction]},
                {'type': 'wait', 'duration': int(duration * 1000)},
                {'type': 'key', 'action': 'keyUp', 'key': key_map[direction]}
            ])
            
    def add_turn_command(self, direction: str, degrees: int):
        """Add turn command to queue"""
        pixels = degrees * 5
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
        ])
        
    def add_weapon_command(self, weapon_num: int):
        """Add weapon switch command to queue"""
        self.command_queue.extend([
            {'type': 'key', 'action': 'press', 'key': str(weapon_num)},
        ])
        
    def add_escape_command(self):
        """Add ESC key command to queue"""
        self.command_queue.extend([
            {'type': 'key', 'action': 'press', 'key': 'escape'},
        ])
        
    def add_enter_command(self):
        """Add Enter key command to queue"""
        self.command_queue.extend([
            {'type': 'key', 'action': 'press', 'key': 'enter'},
        ])

# Global controller instance
doom_controller = AppleScriptDoomController()