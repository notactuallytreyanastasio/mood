#!/usr/bin/env python3
"""
DOOM-COBOL Bridge Runner
Runs on host to bridge between Docker containers and real DOOM process
"""

import sys
import os
import time
import logging
import argparse

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from doom_memory import DoomMemoryReader
from mvs_connector import MVSConnector
from doom_controller import DoomController

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HostBridge:
    """Bridge that runs on host system"""
    
    def __init__(self):
        self.running = True
        self.doom_reader = None
        self.controller = None
        
    def find_doom(self):
        """Keep trying to find DOOM process"""
        while self.running and not self.doom_reader:
            try:
                self.doom_reader = DoomMemoryReader()
                if self.doom_reader.process:
                    logger.info(f"Found DOOM process: PID {self.doom_reader.pid}")
                    return True
            except Exception as e:
                logger.debug(f"DOOM not found: {e}")
            
            logger.info("Waiting for DOOM to start...")
            time.sleep(2)
            
        return False
        
    def run(self):
        """Main bridge loop"""
        logger.info("DOOM-COBOL Host Bridge starting...")
        
        # Find DOOM
        if not self.find_doom():
            return
            
        # Initialize controller
        self.controller = DoomController()
        
        logger.info("Bridge ready - DOOM will respond to COBOL commands!")
        
        # For now, we'll poll for commands from a file
        # In production, this would connect to the Docker network
        command_file = "/tmp/doom-cobol-commands.txt"
        
        while self.running:
            try:
                # Check if DOOM is still running
                if self.doom_reader.process and not self.doom_reader.process.is_running():
                    logger.warning("DOOM process ended")
                    break
                    
                # Check for commands
                if os.path.exists(command_file):
                    with open(command_file, 'r') as f:
                        commands = f.readlines()
                    
                    # Process commands
                    for cmd in commands:
                        cmd = cmd.strip()
                        if cmd:
                            logger.info(f"Executing: {cmd}")
                            self.process_command(cmd)
                    
                    # Clear command file
                    os.remove(command_file)
                    
                time.sleep(0.1)  # 10Hz polling
                
            except KeyboardInterrupt:
                logger.info("Shutdown requested")
                self.running = False
            except Exception as e:
                logger.error(f"Bridge error: {e}")
                
    def process_command(self, cmd):
        """Process a command string"""
        parts = cmd.split()
        if not parts:
            return
            
        action = parts[0].upper()
        
        if action == "MOVE":
            if len(parts) >= 2:
                direction = parts[1].upper()
                duration = float(parts[2]) if len(parts) > 2 else 0.5
                self.move(direction, duration)
                
        elif action == "TURN":
            if len(parts) >= 3:
                direction = parts[1].upper()
                degrees = int(parts[2])
                self.turn(direction, degrees)
                
        elif action == "SHOOT":
            count = int(parts[1]) if len(parts) > 1 else 1
            self.shoot(count)
            
        elif action == "USE":
            self.use()
            
    def move(self, direction, duration):
        """Execute movement"""
        import pyautogui
        
        key_map = {
            'FORWARD': 'w',
            'BACK': 's',
            'LEFT': 'a',
            'RIGHT': 'd'
        }
        
        if direction in key_map:
            key = key_map[direction]
            logger.debug(f"Move {direction} for {duration}s")
            pyautogui.keyDown(key)
            time.sleep(duration)
            pyautogui.keyUp(key)
            
    def turn(self, direction, degrees):
        """Execute turn"""
        import pyautogui
        
        # Adjust mouse sensitivity as needed
        pixels = degrees * 5
        dx = pixels if direction == 'RIGHT' else -pixels
        
        logger.debug(f"Turn {direction} {degrees} degrees")
        pyautogui.moveRel(dx, 0, duration=0.1)
        
    def shoot(self, count):
        """Execute shoot"""
        import pyautogui
        
        logger.debug(f"Shoot {count} times")
        for _ in range(count):
            pyautogui.click()
            time.sleep(0.1)
            
    def use(self):
        """Execute use/open"""
        import pyautogui
        
        logger.debug("Use/Open")
        pyautogui.press('space')  # Or 'e' depending on DOOM config


def main():
    parser = argparse.ArgumentParser(description='DOOM-COBOL Host Bridge')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    bridge = HostBridge()
    
    try:
        bridge.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()