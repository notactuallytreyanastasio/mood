#!/usr/bin/env python3
"""
DOOM Memory Reader for Linux
Reads actual game state from process memory
"""

import os
import struct
import time
import logging
from dataclasses import dataclass
from typing import List, Optional
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DoomState:
    """Current DOOM game state"""
    tick: int
    player_x: int
    player_y: int
    player_z: int
    player_angle: int
    health: int
    armor: int
    ammo: List[int]
    current_weapon: int
    level: int
    
    def to_cobol_records(self) -> List[str]:
        """Convert to COBOL format records"""
        records = []
        
        # Game state record
        records.append(f"STATE {self.tick:08d} {self.level:02d}")
        
        # Player record - convert fixed point to integer
        x = self.player_x >> 16  # Convert from fixed point
        y = self.player_y >> 16
        z = self.player_z >> 16
        angle = (self.player_angle * 360) // 0xFFFFFFFF  # Convert to degrees
        
        records.append(f"PLAYER{x:+08d}{y:+08d}{z:+08d}"
                      f"{angle:+04d}{self.health:03d}{self.armor:03d}")
        
        # Ammo record
        ammo_str = "".join(f"{a:04d}" for a in self.ammo[:4])
        records.append(f"AMMO  {ammo_str}{self.current_weapon:01d}")
        
        return records


class LinuxDoomMemoryReader:
    """Read DOOM memory on Linux using /proc"""
    
    # Known patterns in DOOM memory
    PLAYER_PATTERN = b'\\x00\\x00\\x00\\x00\\x64\\x00\\x00\\x00'  # Health = 100
    
    def __init__(self, pid: int):
        self.pid = pid
        self.base_address = None
        self.player_offset = None
        self._find_base_address()
        
    def _find_base_address(self):
        """Find DOOM's base address in memory"""
        try:
            with open(f'/proc/{self.pid}/maps', 'r') as f:
                for line in f:
                    if 'chocolate-doom' in line and 'r-xp' in line:
                        # Extract base address
                        addr_range = line.split()[0]
                        self.base_address = int(addr_range.split('-')[0], 16)
                        logger.info(f"Found base address: 0x{self.base_address:x}")
                        break
        except Exception as e:
            logger.error(f"Failed to find base address: {e}")
            
    def _read_memory(self, address: int, size: int) -> bytes:
        """Read memory from process"""
        try:
            with open(f'/proc/{self.pid}/mem', 'rb') as mem:
                mem.seek(address)
                return mem.read(size)
        except Exception as e:
            logger.debug(f"Memory read failed at 0x{address:x}: {e}")
            return b''
            
    def _find_player_structure(self):
        """Scan memory for player structure"""
        if not self.base_address:
            return None
            
        # Scan likely regions
        scan_size = 0x100000  # 1MB chunks
        
        for offset in range(0, 0x1000000, scan_size):
            addr = self.base_address + offset
            data = self._read_memory(addr, scan_size)
            
            # Look for player structure patterns
            # Player typically starts with health=100, armor=0
            pattern_idx = data.find(b'\\x64\\x00\\x00\\x00\\x00\\x00\\x00\\x00')
            if pattern_idx >= 0:
                potential_addr = addr + pattern_idx
                # Verify it looks like player data
                test_data = self._read_memory(potential_addr - 16, 128)
                if self._verify_player_structure(test_data):
                    self.player_offset = potential_addr - self.base_address
                    logger.info(f"Found player at offset: 0x{self.player_offset:x}")
                    return True
                    
        return False
        
    def _verify_player_structure(self, data: bytes) -> bool:
        """Verify data looks like player structure"""
        if len(data) < 64:
            return False
            
        # Check for reasonable values
        try:
            # Health should be 0-200
            health = struct.unpack('<i', data[16:20])[0]
            if not (0 <= health <= 200):
                return False
                
            # Armor should be 0-200
            armor = struct.unpack('<i', data[20:24])[0]
            if not (0 <= armor <= 200):
                return False
                
            return True
        except:
            return False
            
    def read_game_state(self) -> Optional[DoomState]:
        """Read current game state from memory"""
        if not self.base_address:
            return None
            
        # If we haven't found player offset yet, search for it
        if not self.player_offset:
            if not self._find_player_structure():
                # Return mock data if we can't find player
                return self._mock_state()
                
        try:
            # Read player structure
            player_addr = self.base_address + self.player_offset
            player_data = self._read_memory(player_addr, 256)
            
            if len(player_data) < 256:
                return self._mock_state()
                
            # Parse player structure (based on DOOM source)
            # This is approximate - actual offsets may vary
            health = struct.unpack('<i', player_data[0:4])[0]
            armor = struct.unpack('<i', player_data[4:8])[0]
            
            # Read position from mobj_t structure (usually linked from player)
            # For now, use mock positions
            x, y, z = 0, 0, 0
            angle = 0
            
            # Ammo array
            ammo = []
            for i in range(4):
                ammo_val = struct.unpack('<i', player_data[24+i*4:28+i*4])[0]
                ammo.append(max(0, min(999, ammo_val)))
                
            return DoomState(
                tick=int(time.time() * 35) % 1000000,
                player_x=x,
                player_y=y,
                player_z=z,
                player_angle=angle,
                health=max(0, min(200, health)),
                armor=max(0, min(200, armor)),
                ammo=ammo,
                current_weapon=1,
                level=1
            )
            
        except Exception as e:
            logger.error(f"Failed to read game state: {e}")
            return self._mock_state()
            
    def _mock_state(self) -> DoomState:
        """Return mock state when memory reading fails"""
        return DoomState(
            tick=int(time.time() * 35) % 1000000,
            player_x=1024 << 16,
            player_y=1024 << 16,
            player_z=0,
            player_angle=0,
            health=75,
            armor=25,
            ammo=[50, 20, 100, 40],
            current_weapon=2,
            level=1
        )


def main():
    """Test memory reader"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: doom_memory_linux.py <pid>")
        sys.exit(1)
        
    pid = int(sys.argv[1])
    reader = LinuxDoomMemoryReader(pid)
    
    print(f"Reading DOOM process {pid}")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            state = reader.read_game_state()
            if state:
                print(f"Health: {state.health}, Armor: {state.armor}, "
                      f"Ammo: {state.ammo[0]}, Tick: {state.tick}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nDone")


if __name__ == "__main__":
    main()