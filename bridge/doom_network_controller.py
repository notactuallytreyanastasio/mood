#!/usr/bin/env python3
"""
Network controller for modified DOOM
Sends UDP commands to DOOM's network input port
"""

import socket
import time
import logging
import threading
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DoomNetworkController:
    """Send commands to modified DOOM via UDP"""
    
    def __init__(self, host='localhost', port=31338):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.command_queue = []
        self.running = True
        self._start_executor()
        
    def _start_executor(self):
        """Start command executor thread"""
        self.executor_thread = threading.Thread(target=self._execute_loop, daemon=True)
        self.executor_thread.start()
        
    def _execute_loop(self):
        """Process queued commands"""
        while self.running:
            if self.command_queue:
                cmd = self.command_queue.pop(0)
                self._send_command(cmd['command'])
                
                # Handle duration-based commands
                if 'duration' in cmd and cmd['duration'] > 0:
                    time.sleep(cmd['duration'])
                    # Send stop command if needed
                    if 'stop_command' in cmd:
                        self._send_command(cmd['stop_command'])
                        
            time.sleep(0.01)  # 100Hz check rate
            
    def _send_command(self, command: str):
        """Send raw command to DOOM"""
        try:
            self.socket.sendto(command.encode('ascii'), (self.host, self.port))
            logger.debug(f"Sent: {command}")
        except Exception as e:
            logger.error(f"Send failed: {e}")
            
    def move(self, direction: str, duration: float = 0.5):
        """Move player in direction for duration seconds"""
        direction = direction.upper()
        if direction not in ['FORWARD', 'BACK', 'LEFT', 'RIGHT']:
            return
            
        self.command_queue.append({
            'command': f"{direction} {int(duration * 1000)}",
            'duration': 0  # Duration handled by DOOM
        })
        
    def turn(self, direction: str, degrees: int = 45):
        """Turn player by degrees"""
        direction = direction.upper()
        if direction == 'LEFT':
            command = f"TURNLEFT {degrees}"
        elif direction == 'RIGHT':
            command = f"TURNRIGHT {degrees}"
        else:
            return
            
        self.command_queue.append({
            'command': command,
            'duration': 0
        })
        
    def shoot(self, count: int = 1):
        """Fire weapon count times"""
        for _ in range(count):
            self.command_queue.append({
                'command': 'SHOOT',
                'duration': 0.1
            })
            
    def use(self):
        """Press use key (open doors, etc)"""
        self.command_queue.append({
            'command': 'USE',
            'duration': 0
        })
        
    def send_raw(self, command: str):
        """Send raw command string"""
        self.command_queue.append({
            'command': command,
            'duration': 0
        })
        
    def stop(self):
        """Stop the controller"""
        self.running = False
        self.socket.close()


class DoomCommandInterface:
    """High-level interface matching COBOL commands"""
    
    def __init__(self, controller: DoomNetworkController):
        self.controller = controller
        
    def process_command(self, command: str) -> str:
        """Process COBOL-style command"""
        parts = command.upper().split()
        if not parts:
            return "ERROR: Empty command"
            
        action = parts[0]
        
        if action == "MOVE":
            if len(parts) < 2:
                return "ERROR: MOVE requires direction"
            direction = parts[1]
            duration = float(parts[2]) if len(parts) > 2 else 0.5
            self.controller.move(direction, duration)
            return f"OK: Moving {direction} for {duration}s"
            
        elif action == "TURN":
            if len(parts) < 2:
                return "ERROR: TURN requires direction"
            direction = parts[1]
            degrees = int(parts[2]) if len(parts) > 2 else 45
            self.controller.turn(direction, degrees)
            return f"OK: Turning {direction} {degrees} degrees"
            
        elif action == "SHOOT":
            count = int(parts[1]) if len(parts) > 1 else 1
            self.controller.shoot(count)
            return f"OK: Shooting {count} times"
            
        elif action == "USE":
            self.controller.use()
            return "OK: Using"
            
        else:
            return f"ERROR: Unknown command: {action}"


def test_controller():
    """Test the network controller"""
    print("DOOM Network Controller Test")
    print("=" * 50)
    print()
    print("Make sure modified DOOM is running with network input enabled")
    print("Commands will be sent to UDP port 31338")
    print()
    
    controller = DoomNetworkController()
    interface = DoomCommandInterface(controller)
    
    # Test sequence
    test_commands = [
        "MOVE FORWARD 2",
        "TURN RIGHT 90",
        "MOVE FORWARD 1",
        "SHOOT 3",
        "TURN LEFT 45",
        "USE",
        "MOVE BACK 1"
    ]
    
    print("Running test sequence...")
    for cmd in test_commands:
        print(f"\n> {cmd}")
        result = interface.process_command(cmd)
        print(f"< {result}")
        time.sleep(1)
        
    print("\nTest complete!")
    controller.stop()


if __name__ == "__main__":
    test_controller()