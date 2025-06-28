#!/usr/bin/env python3
"""
Simulate DOOM writing state to /tmp/doom_state.dat
For testing the COBOL loop without needing actual DOOM
"""

import time
import random

def write_state(tick, health, armor, x, y, angle):
    """Write DOOM state in COBOL format"""
    with open('/tmp/doom_state.dat', 'w') as f:
        # STATE record
        f.write(f"STATE {tick:08d} 01\n")
        
        # PLAYER record
        f.write(f"PLAYER{x:+08d}{y:+08d}+0000000{angle:+04d}{health:03d}{armor:03d}\n")
        
        # AMMO record  
        f.write("AMMO  0050002001000040 2\n")
        
        # Add some enemies if health is good
        if health > 50:
            enemy_count = random.randint(1, 3)
            for i in range(enemy_count):
                ex = x + random.randint(-500, 500)
                ey = y + random.randint(-500, 500)
                dist = abs(ex - x) + abs(ey - y)
                f.write(f"ENEMY 09 100 {ex:+08d} {ey:+08d} {dist:05d}\n")

def main():
    print("DOOM State Simulator")
    print("=" * 50)
    print("Writing state to /tmp/doom_state.dat")
    print("Press Ctrl+C to stop")
    print()
    
    tick = 0
    health = 100
    armor = 50
    x, y = 1024, 1024
    angle = 90
    
    try:
        while True:
            tick += 1
            
            # Simulate game events
            if tick % 10 == 0:
                # Take damage occasionally
                damage = random.randint(0, 20)
                health = max(10, health - damage)
                if damage > 0:
                    print(f"! Took {damage} damage, health now {health}")
            
            if tick % 20 == 0:
                # Find health pack
                heal = random.randint(10, 25)
                health = min(100, health + heal)
                print(f"+ Found health, restored {heal}, health now {health}")
            
            # Simulate movement
            x += random.randint(-50, 50)
            y += random.randint(-50, 50)
            angle = (angle + random.randint(-30, 30)) % 360
            
            # Write state
            write_state(tick, health, armor, x, y, angle)
            
            # Show current state
            print(f"Tick {tick}: Health={health}, Pos=({x},{y}), Angle={angle}")
            
            # Wait before next update
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nSimulation stopped")

if __name__ == "__main__":
    main()