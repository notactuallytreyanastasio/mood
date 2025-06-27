#!/usr/bin/env python3
"""
DOOM-COBOL Bridge Service
Connects real DOOM process to z/OS COBOL brain
"""

import time
import struct
import psutil
import ftplib
import argparse
import logging
from dataclasses import dataclass
from typing import Optional, List, Tuple
import mmap
import os

# Platform-specific imports
try:
    from Xlib import X, display as x_display
    import pyautogui
    PLATFORM = 'linux'
except ImportError:
    import win32api
    import win32con
    import win32process
    PLATFORM = 'windows'


@dataclass
class DoomState:
    """Current DOOM game state"""
    tick: int
    player_x: int
    player_y: int
    player_z: int
    player_angle: int  # 0-359 degrees
    health: int
    armor: int
    ammo: List[int]  # 6 weapon types
    current_weapon: int
    level: int
    

@dataclass
class DoomEntity:
    """Visible entity (monster/item)"""
    entity_type: str  # M=Monster, I=Item, D=Door
    subtype: int
    x: int
    y: int
    z: int
    distance: int
    angle: int
    health: int
    state: str  # A=Active, D=Dead, I=Idle


@dataclass
class DoomCommand:
    """Command from COBOL to execute"""
    cmd_type: str  # K=Key, M=Mouse
    action: str    # P=Press, R=Release
    code: str      # Key code or mouse button
    mouse_dx: int
    mouse_dy: int


class DoomMemoryReader:
    """Read DOOM process memory for game state"""
    
    # Memory offsets for DOOM 1.9 (these need to be discovered)
    PLAYER_BASE = 0x00000000  # TODO: Find actual offset
    THING_LIST = 0x00000000   # TODO: Find actual offset
    
    def __init__(self, process_name="doom"):
        self.process = self._find_doom_process(process_name)
        self.pid = self.process.pid
        
    def _find_doom_process(self, name):
        """Find DOOM process by name"""
        for proc in psutil.process_iter(['pid', 'name']):
            if name.lower() in proc.info['name'].lower():
                logging.info(f"Found DOOM process: {proc.info}")
                return proc
        raise RuntimeError(f"DOOM process '{name}' not found")
        
    def read_game_state(self) -> DoomState:
        """Extract current game state from memory"""
        # TODO: Implement actual memory reading
        # For now, return mock data
        return DoomState(
            tick=int(time.time() * 35) % 1000000,
            player_x=1024,
            player_y=1024,
            player_z=0,
            player_angle=90,
            health=100,
            armor=50,
            ammo=[50, 20, 100, 40, 20, 10],
            current_weapon=2,
            level=1
        )
        
    def read_visible_entities(self) -> List[DoomEntity]:
        """Extract visible monsters and items"""
        # TODO: Implement actual entity scanning
        # For now, return mock data
        return [
            DoomEntity('M', 1, 1200, 1024, 0, 176, 0, 60, 'A'),
            DoomEntity('M', 2, 800, 900, 0, 224, -45, 100, 'A'),
            DoomEntity('I', 10, 1100, 1100, 0, 100, 45, 0, 'I'),
        ]


class MVSConnector:
    """Handle FTP communication with z/OS"""
    
    def __init__(self, host, user='HERC01', password='CUL8TR'):
        self.host = host
        self.user = user
        self.password = password
        self.ftp = None
        self._connect()
        
    def _connect(self):
        """Establish FTP connection"""
        self.ftp = ftplib.FTP(self.host)
        self.ftp.login(self.user, self.password)
        self.ftp.sendcmd('SITE RECFM=FB')
        logging.info(f"Connected to MVS at {self.host}")
        
    def _format_state_record(self, state: DoomState) -> bytes:
        """Format game state as COBOL-readable 80-byte record"""
        # Format: TTTTTTTTTXXXXXYYYYYZZZZZAAAHHHAAAAMMMMMMMMMMMMMMMMMMMMWLL
        record = (
            f"{state.tick:09d}"
            f"{state.player_x:+010d}"
            f"{state.player_y:+010d}"
            f"{state.player_z:+010d}"
            f"{state.player_angle:+04d}"
            f"{state.health:03d}"
            f"{state.armor:03d}"
            f"{''.join(f'{a:03d}' for a in state.ammo)}"
            f"{state.current_weapon:01d}"
            f"{state.level:02d}"
        )
        return record.ljust(80).encode('cp037')  # EBCDIC encoding
        
    def upload_game_state(self, state: DoomState):
        """Upload current game state to DOOM.STATE dataset"""
        data = self._format_state_record(state)
        self.ftp.storbinary('STOR DOOM.STATE', data)
        
    def upload_entities(self, entities: List[DoomEntity]):
        """Upload visible entities to DOOM.ENTITIES dataset"""
        records = []
        for ent in entities:
            # Format: TSSXXXXXXXXXYYYYYYYYY...
            record = (
                f"{ent.entity_type}"
                f"{ent.subtype:02d}"
                f"{ent.x:+010d}"
                f"{ent.y:+010d}"
                f"{ent.z:+010d}"
                f"{ent.distance:05d}"
                f"{ent.angle:+04d}"
                f"{ent.health:03d}"
                f"{ent.state}"
            )
            records.append(record.ljust(120).encode('cp037'))
            
        data = b''.join(records)
        self.ftp.storbinary('STOR DOOM.ENTITIES', data)
        
    def download_commands(self) -> List[DoomCommand]:
        """Download commands from DOOM.COMMANDS dataset"""
        commands = []
        data = []
        
        def handle_data(block):
            data.append(block)
            
        try:
            self.ftp.retrbinary('RETR DOOM.COMMANDS', handle_data)
            full_data = b''.join(data)
            
            # Parse 80-byte records
            for i in range(0, len(full_data), 80):
                record = full_data[i:i+80].decode('cp037').strip()
                if record:
                    # Format: TAKKKK+DDD+DDD
                    cmd = DoomCommand(
                        cmd_type=record[0],
                        action=record[1],
                        code=record[2:6].strip(),
                        mouse_dx=int(record[6:10]) if record[6:10].strip() else 0,
                        mouse_dy=int(record[10:14]) if record[10:14].strip() else 0
                    )
                    commands.append(cmd)
        except ftplib.error_perm:
            # No commands available
            pass
            
        return commands


class DoomController:
    """Send keyboard/mouse input to DOOM"""
    
    def __init__(self):
        if PLATFORM == 'linux':
            self.display = x_display.Display()
            self.doom_window = self._find_doom_window()
        else:
            self.doom_window = self._find_doom_window_windows()
            
    def _find_doom_window(self):
        """Find DOOM window on Linux"""
        root = self.display.screen().root
        window_ids = root.get_full_property(
            self.display.intern_atom('_NET_CLIENT_LIST'),
            X.AnyPropertyType
        ).value
        
        for window_id in window_ids:
            window = self.display.create_resource_object('window', window_id)
            name = window.get_wm_name()
            if name and 'doom' in name.lower():
                logging.info(f"Found DOOM window: {name}")
                return window
                
        raise RuntimeError("DOOM window not found")
        
    def _find_doom_window_windows(self):
        """Find DOOM window on Windows"""
        # TODO: Implement Windows window finding
        pass
        
    def execute_command(self, cmd: DoomCommand):
        """Execute a command from COBOL"""
        logging.debug(f"Executing: {cmd}")
        
        if cmd.cmd_type == 'K':
            # Keyboard command
            if cmd.action == 'P':
                pyautogui.keyDown(cmd.code.strip().lower())
            else:
                pyautogui.keyUp(cmd.code.strip().lower())
                
        elif cmd.cmd_type == 'M':
            # Mouse command
            if cmd.code.strip() == 'MOVE':
                pyautogui.moveRel(cmd.mouse_dx, cmd.mouse_dy)
            elif cmd.action == 'P':
                pyautogui.mouseDown()
            else:
                pyautogui.mouseUp()


class DoomBridge:
    """Main bridge orchestrator"""
    
    def __init__(self, mvs_host, tick_rate=10):
        self.memory_reader = DoomMemoryReader()
        self.mvs = MVSConnector(mvs_host)
        self.controller = DoomController()
        self.tick_rate = tick_rate
        self.running = True
        
    def run(self):
        """Main bridge loop"""
        logging.info("DOOM-COBOL Bridge started")
        
        while self.running:
            try:
                # Read DOOM state
                state = self.memory_reader.read_game_state()
                entities = self.memory_reader.read_visible_entities()
                
                # Upload to MVS
                self.mvs.upload_game_state(state)
                self.mvs.upload_entities(entities)
                
                # Wait for COBOL processing
                time.sleep(0.2)  # Give COBOL time to process
                
                # Download and execute commands
                commands = self.mvs.download_commands()
                for cmd in commands:
                    self.controller.execute_command(cmd)
                    
                # Rate limiting
                time.sleep(1.0 / self.tick_rate)
                
            except KeyboardInterrupt:
                logging.info("Bridge shutdown requested")
                self.running = False
            except Exception as e:
                logging.error(f"Bridge error: {e}")
                time.sleep(1.0)


def main():
    parser = argparse.ArgumentParser(description='DOOM-COBOL Bridge Service')
    parser.add_argument('--mvs-host', default='localhost', help='MVS host address')
    parser.add_argument('--tick-rate', type=int, default=10, help='Updates per second')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    bridge = DoomBridge(args.mvs_host, args.tick_rate)
    bridge.run()


if __name__ == '__main__':
    main()