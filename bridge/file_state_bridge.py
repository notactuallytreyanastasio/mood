#!/usr/bin/env python3
"""
DOOM State Bridge using file exchange
Simpler than memory reading, works everywhere
"""

import json
import time
import os
import logging
import subprocess
from dataclasses import dataclass, asdict
from typing import List, Optional
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DoomState:
    """Current DOOM game state"""
    tick: int
    health: int
    armor: int
    ammo: List[int]
    current_weapon: int
    level: int
    x: int = 0
    y: int = 0
    z: int = 0
    angle: int = 0
    
    def to_cobol_records(self) -> List[str]:
        """Convert to COBOL format records"""
        records = []
        
        # Game state record
        records.append(f"STATE {self.tick:08d} {self.level:02d}")
        
        # Player record
        records.append(f"PLAYER{self.x:+08d}{self.y:+08d}{self.z:+08d}"
                      f"{self.angle:+04d}{self.health:03d}{self.armor:03d}")
        
        # Ammo record
        ammo_str = "".join(f"{a:04d}" for a in self.ammo[:4])
        records.append(f"AMMO  {ammo_str}{self.current_weapon:01d}")
        
        return records


class FileStateBridge:
    """Bridge using file for state exchange"""
    
    def __init__(self, state_file="doom_state.json", command_file="doom_commands.txt"):
        self.state_file = state_file
        self.command_file = command_file
        self.running = False
        self.last_state = None
        
    def start(self):
        """Start the bridge"""
        self.running = True
        
        # Start threads
        state_thread = threading.Thread(target=self._read_state_loop, daemon=True)
        command_thread = threading.Thread(target=self._process_commands_loop, daemon=True)
        
        state_thread.start()
        command_thread.start()
        
        logger.info("File state bridge started")
        logger.info(f"Reading state from: {self.state_file}")
        logger.info(f"Reading commands from: {self.command_file}")
        
    def _read_state_loop(self):
        """Continuously read game state from file"""
        while self.running:
            try:
                if os.path.exists(self.state_file):
                    with open(self.state_file, 'r') as f:
                        data = json.load(f)
                        
                    self.last_state = DoomState(**data)
                    
                    # Process with COBOL AI
                    self._process_state(self.last_state)
                    
            except Exception as e:
                logger.debug(f"State read error: {e}")
                
            time.sleep(0.1)  # 10Hz
            
    def _process_state(self, state: DoomState):
        """Process state with AI logic"""
        commands = []
        
        # Simple AI logic (mimicking COBOL)
        if state.health < 30:
            logger.info("AI: Survival mode - retreating")
            commands.append("MOVE BACK 1")
            commands.append("TURN LEFT 90")
            
        elif state.health > 70 and state.ammo[0] > 10:
            logger.info("AI: Combat mode")
            commands.append("MOVE FORWARD 0.5")
            commands.append("SHOOT 2")
            
        else:
            logger.info("AI: Exploration mode")
            commands.append("MOVE FORWARD 1")
            commands.append("TURN RIGHT 30")
            
        # Send commands
        for cmd in commands:
            self._send_command(cmd)
            time.sleep(0.1)
            
    def _send_command(self, command: str):
        """Send command to COBOL interface"""
        try:
            subprocess.run(
                f'echo "{command}" | nc localhost 9999',
                shell=True,
                capture_output=True,
                timeout=1
            )
            logger.debug(f"Sent: {command}")
        except Exception as e:
            logger.error(f"Command error: {e}")
            
    def _process_commands_loop(self):
        """Process commands from file (alternative input method)"""
        while self.running:
            try:
                if os.path.exists(self.command_file):
                    with open(self.command_file, 'r') as f:
                        commands = f.readlines()
                        
                    # Clear file
                    open(self.command_file, 'w').close()
                    
                    # Execute commands
                    for cmd in commands:
                        cmd = cmd.strip()
                        if cmd:
                            self._send_command(cmd)
                            time.sleep(0.1)
                            
            except Exception as e:
                logger.debug(f"Command read error: {e}")
                
            time.sleep(0.5)
            
    def get_state(self) -> Optional[DoomState]:
        """Get last known state"""
        return self.last_state


def create_mock_state_writer():
    """Create a mock state writer for testing"""
    tick = 0
    health = 100
    armor = 50
    ammo = [50, 20, 100, 40]
    
    logger.info("Starting mock state writer")
    logger.info("This simulates DOOM writing state to file")
    
    while True:
        # Simulate game events
        tick += 1
        
        # Random damage
        if tick % 10 == 0:
            health = max(0, health - 5)
            
        # Random ammo use
        if tick % 5 == 0:
            ammo[0] = max(0, ammo[0] - 2)
            
        # Write state
        state = {
            "tick": tick,
            "health": health,
            "armor": armor,
            "ammo": ammo,
            "current_weapon": 2,
            "level": 1,
            "x": 1000 + tick * 10,
            "y": 1000,
            "z": 0,
            "angle": (tick * 5) % 360
        }
        
        with open("doom_state.json", "w") as f:
            json.dump(state, f)
            
        time.sleep(0.1)  # 10Hz


def main():
    """Run the file state bridge"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--mock":
        create_mock_state_writer()
        return
        
    print("DOOM File State Bridge")
    print("=" * 50)
    print()
    print("This bridge reads DOOM state from doom_state.json")
    print("and sends AI commands to the COBOL interface")
    print()
    print("Make sure:")
    print("1. COBOL interface is running (./run_local_cobol.sh)")
    print("2. DOOM is writing state to doom_state.json")
    print()
    print("To test with mock data: python3 file_state_bridge.py --mock")
    print()
    
    bridge = FileStateBridge()
    bridge.start()
    
    try:
        while True:
            time.sleep(1)
            state = bridge.get_state()
            if state:
                print(f"State: Health={state.health}, Ammo={state.ammo[0]}, Tick={state.tick}")
                
    except KeyboardInterrupt:
        print("\nShutting down...")
        bridge.running = False


if __name__ == "__main__":
    main()