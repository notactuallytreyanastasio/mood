#!/usr/bin/env python3
"""
Mock MVS for testing without a real mainframe
Simulates FTP server and dataset operations
"""

import threading
import socket
import time
import os
from dataclasses import dataclass
from typing import List, Dict
import json

@dataclass
class MockDataset:
    """Simulated MVS dataset"""
    name: str
    records: List[bytes]
    recfm: str = 'FB'
    lrecl: int = 80

class MockMVS:
    """Mock mainframe for development"""
    
    def __init__(self):
        self.datasets: Dict[str, MockDataset] = {
            'DOOM.STATE': MockDataset('DOOM.STATE', [], 'FB', 80),
            'DOOM.ENTITIES': MockDataset('DOOM.ENTITIES', [], 'FB', 120),
            'DOOM.COMMANDS': MockDataset('DOOM.COMMANDS', [], 'FB', 80),
            'DOOM.TACTICS': MockDataset('DOOM.TACTICS', [], 'FB', 100),
        }
        
        # Simulated game state
        self.game_state = {
            'tick': 0,
            'player_x': 1024,
            'player_y': 1024,
            'player_z': 0,
            'player_angle': 90,
            'health': 100,
            'armor': 50,
            'ammo': [50, 20, 100, 40, 20, 10],
            'current_weapon': 2,
            'level': 1
        }
        
    def update_game_state(self):
        """Simulate game state updates"""
        self.game_state['tick'] += 1
        
        # Format as COBOL record
        record = (
            f"{self.game_state['tick']:09d}"
            f"{self.game_state['player_x']:+010d}"
            f"{self.game_state['player_y']:+010d}"
            f"{self.game_state['player_z']:+010d}"
            f"{self.game_state['player_angle']:+04d}"
            f"{self.game_state['health']:03d}"
            f"{self.game_state['armor']:03d}"
            f"{''.join(f'{a:03d}' for a in self.game_state['ammo'])}"
            f"{self.game_state['current_weapon']:01d}"
            f"{self.game_state['level']:02d}"
        )
        
        # Store in dataset
        self.datasets['DOOM.STATE'].records = [record.ljust(80).encode('cp037')]
        
    def process_commands(self):
        """Process commands from DOOM.COMMANDS"""
        if not self.datasets['DOOM.COMMANDS'].records:
            return
            
        for record in self.datasets['DOOM.COMMANDS'].records:
            cmd = record.decode('cp037').strip()
            if not cmd:
                continue
                
            # Parse command
            cmd_type = cmd[0]
            action = cmd[1]
            code = cmd[2:6].strip()
            
            print(f"Mock MVS processing: {cmd_type} {action} {code}")
            
            # Simulate state changes
            if cmd_type == 'K' and action == 'P':
                if code == 'W':
                    self.game_state['player_y'] -= 10
                elif code == 'S':
                    self.game_state['player_y'] += 10
                elif code == 'A':
                    self.game_state['player_x'] -= 10
                elif code == 'D':
                    self.game_state['player_x'] += 10
                    
            elif cmd_type == 'M' and code == 'MOVE':
                mouse_x = int(cmd[6:10]) if cmd[6:10].strip() else 0
                self.game_state['player_angle'] += mouse_x // 10
                
        # Clear commands after processing
        self.datasets['DOOM.COMMANDS'].records = []
        
    def run_background_updates(self):
        """Background thread to simulate game updates"""
        while True:
            self.update_game_state()
            self.process_commands()
            time.sleep(0.1)  # 10 Hz updates

# Global mock instance
mock_mvs = MockMVS()

# Start background updates
update_thread = threading.Thread(target=mock_mvs.run_background_updates, daemon=True)
update_thread.start()