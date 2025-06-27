#!/usr/bin/env python3
"""
DOOM-COBOL Bridge Service
Connects real DOOM process to z/OS COBOL brain
"""

import time
import argparse
import logging
import os
import sys

# Import our modules
from doom_memory import DoomMemoryReader, DoomState
from mvs_connector import MVSConnector, DoomCommand
from doom_controller import DoomController




class DoomBridge:
    """Main bridge orchestrator"""
    
    def __init__(self, mvs_host, tick_rate=10, auto_retry=False):
        self.mvs_host = mvs_host
        self.tick_rate = tick_rate
        self.auto_retry = auto_retry
        self.running = True
        self.memory_reader = None
        self.mvs = None
        self.controller = None
        
    def run(self):
        """Main bridge loop"""
        logging.info("DOOM-COBOL Bridge started")
        
        while self.running:
            try:
                # Initialize components if needed
                if not self.memory_reader:
                    logging.info("Initializing memory reader...")
                    self.memory_reader = DoomMemoryReader()
                    if not self.memory_reader.process:
                        logging.warning("DOOM process not found, waiting...")
                        if self.auto_retry:
                            time.sleep(5)
                            continue
                        else:
                            logging.error("DOOM process not found. Please start DOOM.")
                            break
                
                if not self.mvs:
                    logging.info("Connecting to MVS...")
                    self.mvs = MVSConnector(self.mvs_host)
                    if not self.mvs.connect():
                        logging.error("Failed to connect to MVS")
                        if self.auto_retry:
                            time.sleep(5)
                            continue
                        else:
                            break
                
                if not self.controller:
                    logging.info("Initializing controller...")
                    self.controller = DoomController()
                
                # Read DOOM state
                state = self.memory_reader.read_game_state()
                if state:
                    # Upload to MVS
                    self.mvs.upload_game_state(state)
                    
                    # Wait for COBOL processing
                    time.sleep(0.2)
                    
                    # Download and execute commands
                    commands = self.mvs.download_commands()
                    for cmd in commands:
                        self.controller.execute_command(cmd)
                
                # Rate limiting
                time.sleep(1.0 / self.tick_rate)
                
            except KeyboardInterrupt:
                logging.info("Bridge shutdown requested")
                self.running = False
            except Exception as e:
                logging.error(f"Bridge error: {e}")
                if self.auto_retry:
                    time.sleep(5)
                else:
                    break


def main():
    parser = argparse.ArgumentParser(description='DOOM-COBOL Bridge Service')
    parser.add_argument('--mvs-host', default='localhost', help='MVS host address')
    parser.add_argument('--tick-rate', type=int, default=10, help='Updates per second')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    bridge = DoomBridge(args.mvs_host, args.tick_rate)
    bridge.run()


if __name__ == '__main__':
    main()