#!/usr/bin/env python3
"""
Receive state from modified DOOM and bridge to COBOL
"""

import socket
import struct
import time
import threading
import logging
import subprocess
from dataclasses import dataclass
from typing import List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DoomState:
    """DOOM game state from modified engine"""
    tick: int
    health: int
    armor: int
    ammo: List[int]
    weapon: int
    x: int
    y: int
    z: int
    angle: int
    level: int
    enemy_count: int
    enemies: List[dict]


class DoomStateReceiver:
    """Receives state from modified DOOM"""
    
    def __init__(self, port=31337):
        self.port = port
        self.socket = None
        self.running = False
        self.last_state = None
        self.state_callback = None
        
    def start(self, callback=None):
        """Start receiving state"""
        self.state_callback = callback
        self.running = True
        
        # Create UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('0.0.0.0', self.port))
        self.socket.settimeout(0.1)
        
        # Start receiver thread
        thread = threading.Thread(target=self._receive_loop, daemon=True)
        thread.start()
        
        logger.info(f"State receiver listening on UDP port {self.port}")
        
    def _receive_loop(self):
        """Receive state packets"""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(4096)
                state = self._parse_state(data)
                if state:
                    self.last_state = state
                    if self.state_callback:
                        self.state_callback(state)
                        
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Receive error: {e}")
                
    def _parse_state(self, data: bytes) -> Optional[DoomState]:
        """Parse binary state packet"""
        if len(data) < 88:  # Minimum size
            return None
            
        try:
            # Unpack header
            magic, version, tick = struct.unpack('<III', data[0:12])
            if magic != 0x4D4F4F44:  # 'DOOM'
                return None
                
            # Player state
            (health, armor, 
             ammo0, ammo1, ammo2, ammo3,
             weapon, x, y, z, angle, momx, momy,
             level, kills, items, secrets,
             enemy_count) = struct.unpack('<18i', data[12:84])
            
            # Parse enemies
            enemies = []
            offset = 88
            for i in range(min(enemy_count, 16)):
                if offset + 20 <= len(data):
                    enemy_data = struct.unpack('<5i', data[offset:offset+20])
                    enemies.append({
                        'type': enemy_data[0],
                        'health': enemy_data[1],
                        'x': enemy_data[2],
                        'y': enemy_data[3],
                        'distance': enemy_data[4]
                    })
                    offset += 20
                    
            return DoomState(
                tick=tick,
                health=health,
                armor=armor,
                ammo=[ammo0, ammo1, ammo2, ammo3],
                weapon=weapon,
                x=x,
                y=y,
                z=z,
                angle=angle,
                level=level,
                enemy_count=enemy_count,
                enemies=enemies
            )
            
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return None
            
    def stop(self):
        """Stop receiver"""
        self.running = False
        if self.socket:
            self.socket.close()


class COBOLBridge:
    """Bridge between DOOM state and COBOL AI"""
    
    def __init__(self):
        self.receiver = DoomStateReceiver()
        self.last_command_time = 0
        
    def start(self):
        """Start the bridge"""
        self.receiver.start(callback=self.process_state)
        logger.info("COBOL Bridge started")
        
    def process_state(self, state: DoomState):
        """Process state with AI logic"""
        # Rate limit commands
        now = time.time()
        if now - self.last_command_time < 0.2:  # 5Hz max
            return
            
        self.last_command_time = now
        
        # Log state
        logger.info(f"State: Health={state.health}, Enemies={state.enemy_count}, "
                   f"Ammo={state.ammo[0]}, Pos=({state.x>>16},{state.y>>16})")
        
        # AI decision making (mimics COBOL logic)
        commands = []
        
        # Priority 1: Survival (health < 30)
        if state.health < 30:
            logger.info("AI: SURVIVAL MODE")
            commands.extend([
                "MOVE BACK 1",
                "TURN LEFT 90"
            ])
            
        # Priority 2: Combat (enemies nearby)
        elif state.enemy_count > 0 and state.ammo[state.weapon] > 0:
            logger.info(f"AI: COMBAT MODE - {state.enemy_count} enemies")
            
            # Find closest enemy
            if state.enemies:
                closest = min(state.enemies, key=lambda e: e['distance'])
                
                # Calculate angle to enemy
                dx = closest['x'] - state.x
                dy = closest['y'] - state.y
                
                # Simple aiming
                if abs(dx) > abs(dy):
                    commands.append("TURN RIGHT 15" if dx > 0 else "TURN LEFT 15")
                    
                commands.extend([
                    "SHOOT 2",
                    "MOVE LEFT 0.3"  # Strafe
                ])
                
        # Priority 3: Exploration
        else:
            logger.info("AI: EXPLORATION MODE")
            commands.extend([
                "MOVE FORWARD 1",
                "TURN RIGHT 30"
            ])
            
        # Send commands
        for cmd in commands:
            self.send_command(cmd)
            time.sleep(0.05)
            
    def send_command(self, command: str):
        """Send command to COBOL interface"""
        try:
            subprocess.run(
                f'echo "{command}" | nc localhost 9999',
                shell=True,
                capture_output=True,
                timeout=0.5
            )
            logger.debug(f"Sent: {command}")
        except Exception as e:
            logger.error(f"Command failed: {e}")


def main():
    """Run the state receiver bridge"""
    print("DOOM State Receiver Bridge")
    print("=" * 50)
    print()
    print("This receives state from modified DOOM on UDP port 31337")
    print("and sends AI commands to COBOL interface on port 9999")
    print()
    print("Prerequisites:")
    print("1. Modified DOOM running (with state export)")
    print("2. COBOL interface running (./run_local_cobol.sh)")
    print()
    
    input("Press Enter to start...")
    
    bridge = COBOLBridge()
    bridge.start()
    
    try:
        while True:
            time.sleep(1)
            state = bridge.receiver.last_state
            if state:
                print(f"Latest: Health={state.health}, Level=E{1}M{state.level}")
            else:
                print("Waiting for state data...")
                
    except KeyboardInterrupt:
        print("\nShutting down...")
        bridge.receiver.stop()


if __name__ == "__main__":
    main()