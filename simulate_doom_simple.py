#!/usr/bin/env python3
"""
Simple DOOM state simulator - sends UDP packets to SQLite capture
"""

import socket
import struct
import time
import random

# Constants
STATE_PORT = 31337
STATE_MAGIC = 0x4D4F4F44  # 'DOOM'
STATE_VERSION = 1

def main():
    print("Simple DOOM State Simulator")
    print(f"Sending to UDP port {STATE_PORT}")
    
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Initial state
    tick = 0
    
    try:
        while True:
            tick += 1
            
            # Player state (randomized for demo)
            health = random.randint(50, 100)
            armor = random.randint(0, 100)
            x = random.randint(500, 1500) << 16  # Fixed point
            y = random.randint(500, 1500) << 16
            z = 0
            angle = random.randint(0, 360) * 0xFFFFFFFF // 360
            
            # Build minimal packet
            packet = struct.pack('<III', STATE_MAGIC, STATE_VERSION, tick)
            
            # Player data (18 integers)
            packet += struct.pack('<iiiiiiiiiiiiiiiiii',
                health, armor,
                50, 20, 100, 40,  # ammo
                2,  # weapon
                x, y, z,
                angle if angle < 2147483647 else 2147483647,
                0, 0,  # momentum
                1,  # level
                5, 3, 1,  # kills, items, secrets
                2   # enemy count
            )
            
            # Add 2 enemies (5 integers each)
            for i in range(2):
                packet += struct.pack('<iiiii',
                    1,  # type (imp)
                    100,  # health
                    x + (100 << 16),  # position
                    y + (100 << 16),
                    200 << 16  # distance
                )
            
            # Send packet
            sock.sendto(packet, ('localhost', STATE_PORT))
            
            if tick % 35 == 0:
                print(f"Tick {tick}: Sent state (health={health}, pos={x>>16},{y>>16})")
                
            # Also write COBOL file
            with open('/tmp/doom_state.dat', 'w') as f:
                f.write(f"STATE   {tick:08d}01{int(time.time()):08d}\n")
                f.write(f"PLAYER  {x>>16:+08d}{y>>16:+08d}+0000000")
                f.write(f"{(angle * 360 // 0xFFFFFFFF) % 360:+04d}")
                f.write(f"{health:03d}{armor:03d}A\n")
                f.write(f"AMMO    0050002001000040 2\n")
            
            time.sleep(0.1)  # 10 Hz for demo
            
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        sock.close()

if __name__ == "__main__":
    main()