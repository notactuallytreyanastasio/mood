#!/usr/bin/env python3
"""
Read DOOM's memory directly while it's running
Works with chocolate-doom on macOS
"""

import subprocess
import time
import struct
import psutil
import os

def find_doom_process():
    """Find running DOOM process"""
    for proc in psutil.process_iter(['pid', 'name']):
        if 'doom' in proc.info['name'].lower():
            return proc.info['pid']
    return None

def read_process_memory(pid, address, size):
    """Read memory from process using lldb"""
    # Use lldb to read memory
    cmd = f'lldb -p {pid} -o "memory read --size {size} --format x {hex(address)}" -o "quit"'
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            # Parse the output
            lines = result.stdout.split('\n')
            for line in lines:
                if '0x' in line:
                    # Extract hex values
                    parts = line.split()
                    if len(parts) > 2:
                        return parts[2:]  # Return hex values
    except:
        pass
    return None

def main():
    print("DOOM Memory Reader")
    print("==================")
    print("1. Start chocolate-doom in another terminal")
    print("2. This will attempt to read game state from memory")
    print()
    
    # Wait for DOOM to start
    print("Waiting for DOOM process...")
    while True:
        pid = find_doom_process()
        if pid:
            print(f"Found DOOM process: PID {pid}")
            break
        time.sleep(1)
    
    # Common memory locations for game data
    # These are typical locations but may vary
    player_health_addr = 0x100000000  # Example address
    
    print("\nAttempting to read game state...")
    print("(This may require sudo or debugging permissions)")
    
    try:
        while True:
            # Try to read some memory
            data = read_process_memory(pid, player_health_addr, 16)
            if data:
                print(f"Memory at {hex(player_health_addr)}: {data}")
            else:
                print("Could not read memory - may need permissions")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopped")

if __name__ == "__main__":
    main()