#!/usr/bin/env python3
"""
Simulate DOOM state export via UDP
Sends game state packets to port 31337
"""

import socket
import struct
import time
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants from DOOM
STATE_PORT = 31337
STATE_MAGIC = 0x4D4F4F44  # 'DOOM'
STATE_VERSION = 1

def send_state_packet(sock, tick, health, armor, x, y, z, angle, level=1):
    """Send a DOOM state packet via UDP"""
    
    # Build packet (must match x_state.c structure)
    packet = struct.pack('<III', STATE_MAGIC, STATE_VERSION, tick)
    
    # Player state
    packet += struct.pack('<18i',
        health,             # health
        armor,              # armor
        50, 20, 100, 40,   # ammo (bullets, shells, cells, rockets)
        2,                  # weapon (shotgun)
        int(x) & 0x7FFFFFFF,  # x position (fixed point, avoid overflow)
        int(y) & 0x7FFFFFFF,  # y position
        int(z),               # z position
        int(angle),           # angle (BAM units)
        0, 0,                 # momentum
        level,              # level
        random.randint(0, 10),  # kills
        random.randint(0, 5),   # items
        random.randint(0, 2),   # secrets
        random.randint(0, 3)    # enemy_count
    )
    
    # Add a couple enemies
    for i in range(2):
        enemy_type = random.choice([1, 2, 4, 9])  # imp, demon, zombie, etc
        enemy_health = random.randint(20, 100)
        enemy_x = x + (random.randint(-100, 100) << 16)
        enemy_y = y + (random.randint(-100, 100) << 16)
        distance = abs(random.randint(100, 500) << 16)
        
        packet += struct.pack('<5i',
            enemy_type,
            enemy_health,
            int(enemy_x) & 0x7FFFFFFF,
            int(enemy_y) & 0x7FFFFFFF,
            int(distance) & 0x7FFFFFFF
        )
    
    # Send packet
    sock.sendto(packet, ('localhost', STATE_PORT))
    
    # Also write COBOL format to file
    with open('/tmp/doom_state.dat', 'w') as f:
        f.write(f"STATE   {tick:08d}{level:02d}{int(time.time()):08d}\n")
        f.write(f"PLAYER  {x>>16:+08d}{y>>16:+08d}{z>>16:+08d}")
        f.write(f"{int(angle * 360 / 0xFFFFFFFF):+04d}")
        f.write(f"{health:03d}{armor:03d}{'A' if health > 0 else 'D'}\n")
        f.write(f"AMMO    0050002001000040 2\n")

def main():
    logger.info("DOOM State UDP Simulator")
    logger.info(f"Sending to UDP port {STATE_PORT}")
    
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Game state
    tick = 0
    health = 100
    armor = 50
    x = 1024 << 16  # Convert to fixed point
    y = 1024 << 16
    z = 0
    angle = 0x40000000  # 90 degrees in BAM units
    
    logger.info(f"Initial x={x}, y={y} (fixed point)")
    logger.info(f"Initial x>>16={x>>16}, y>>16={y>>16} (map units)")
    
    try:
        while True:
            tick += 1
            
            # Simulate movement
            if tick % 5 == 0:
                x += (random.randint(-10, 10) << 16)
                y += (random.randint(-10, 10) << 16)
                # Keep coordinates in reasonable range
                x = max(-32768 << 16, min(32768 << 16, x))
                y = max(-32768 << 16, min(32768 << 16, y))
                angle = (angle + 0x08000000) & 0xFFFFFFFF  # Turn 45 degrees
            
            # Simulate damage
            if tick % 20 == 0 and health > 0:
                health -= random.randint(0, 10)
                if health < 0:
                    health = 0
                    
            # Simulate picking up items
            if tick % 30 == 0 and health < 100:
                health = min(100, health + 25)
                armor = min(100, armor + 25)
            
            # Send state
            send_state_packet(sock, tick, health, armor, x, y, z, angle)
            
            if tick % 10 == 0:
                logger.info(f"Tick {tick}: Health={health}, Pos=({x>>16},{y>>16})")
            
            time.sleep(1.0 / 35.0)  # 35 Hz like DOOM
            
    except KeyboardInterrupt:
        logger.info("Stopped")
    finally:
        sock.close()

if __name__ == "__main__":
    main()