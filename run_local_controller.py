#!/usr/bin/env python3
"""
Local DOOM controller that runs outside Docker to access the actual display
"""

import socket
import threading
import time
import sys
import os

# Add the cobol-interface directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'cobol-interface'))

from direct_doom import doom_controller

def parse_command(cmd_str):
    """Parse COBOL-style command string"""
    parts = cmd_str.strip().upper().split()
    if not parts:
        return None
        
    cmd = parts[0]
    
    if cmd == 'MOVE' and len(parts) >= 2:
        direction = parts[1]
        duration = float(parts[2]) if len(parts) > 2 else 1.0
        doom_controller.add_move_command(direction, duration)
        return f"Moving {direction} for {duration}s"
        
    elif cmd == 'TURN' and len(parts) >= 3:
        direction = parts[1]
        degrees = int(parts[2])
        doom_controller.add_turn_command(direction, degrees)
        return f"Turning {direction} {degrees} degrees"
        
    elif cmd == 'SHOOT':
        count = int(parts[1]) if len(parts) > 1 else 1
        doom_controller.add_shoot_command(count)
        return f"Shooting {count} times"
        
    elif cmd == 'USE':
        doom_controller.add_use_command()
        return "Using/Opening"
        
    elif cmd == 'WEAPON' and len(parts) >= 2:
        weapon_num = int(parts[1])
        doom_controller.add_weapon_command(weapon_num)
        return f"Switching to weapon {weapon_num}"
        
    elif cmd == 'STATUS':
        return "Local controller active"
        
    else:
        return f"Unknown command: {cmd}"

def handle_client(client_socket, addr):
    """Handle incoming command"""
    try:
        data = client_socket.recv(1024).decode('utf-8').strip()
        print(f"Received: {data}")
        
        response = parse_command(data)
        if response:
            print(f"Response: {response}")
            client_socket.send(f"OK: {response}\n".encode('utf-8'))
        else:
            client_socket.send(b"ERROR: Invalid command\n")
            
    except Exception as e:
        print(f"Error handling client: {e}")
        client_socket.send(f"ERROR: {str(e)}\n".encode('utf-8'))
    finally:
        client_socket.close()

def main():
    """Run local command server"""
    port = 9998  # Different port to avoid conflict with Docker
    
    print(f"Starting local DOOM controller on port {port}")
    print("Make sure DOOM is running and focused!")
    print("\nExample commands:")
    print("  echo 'MOVE FORWARD 2' | nc localhost 9998")
    print("  echo 'TURN RIGHT 90' | nc localhost 9998")
    print("  echo 'SHOOT 3' | nc localhost 9998")
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('localhost', port))
    server.listen(5)
    
    try:
        while True:
            client, addr = server.accept()
            threading.Thread(target=handle_client, args=(client, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.close()

if __name__ == '__main__':
    main()