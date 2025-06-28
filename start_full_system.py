#!/usr/bin/env python3
"""
Start the complete DOOM-COBOL system
Integrates OCR reader, FTP bridge, and COBOL AI
"""

import sys
import time
import threading
import logging
from pathlib import Path

# Add bridge to path
sys.path.insert(0, str(Path(__file__).parent / 'bridge'))
sys.path.insert(0, str(Path(__file__).parent / 'cobol-interface'))

from doom_ocr_reader import DoomOCRReader
from mvs_connector import MVSConnector
from mock_mvs import mock_mvs
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DoomCOBOLBridge:
    """Complete bridge between DOOM and COBOL AI"""
    
    def __init__(self, use_mock_mvs=True):
        self.use_mock_mvs = use_mock_mvs
        self.running = False
        self.ocr_reader = DoomOCRReader()
        self.command_queue = []
        
        if use_mock_mvs:
            logger.info("Using mock MVS")
            self.mvs = None
        else:
            logger.info("Connecting to real MVS")
            self.mvs = MVSConnector('mainframe')
            
    def process_cobol_commands(self, commands: list) -> list:
        """Convert COBOL commands to interface commands"""
        interface_commands = []
        
        for cmd in commands:
            cmd = cmd.strip()
            
            # Parse COBOL command format
            if cmd.startswith('KP'):  # Key press
                key = cmd[2:3]
                interface_commands.append(f"MOVE {'FORWARD' if key == 'W' else 'BACK'} 0.5")
                
            elif cmd.startswith('MR'):  # Mouse right
                pixels = int(cmd[6:11])
                degrees = pixels // 5
                interface_commands.append(f"TURN RIGHT {degrees}")
                
            elif cmd.startswith('ML'):  # Mouse left
                pixels = int(cmd[6:11])
                degrees = pixels // 5
                interface_commands.append(f"TURN LEFT {degrees}")
                
            elif cmd.startswith('MPBTN1'):  # Mouse button (shoot)
                interface_commands.append("SHOOT 1")
                
        return interface_commands
        
    def send_command(self, command: str):
        """Send command to COBOL interface"""
        try:
            result = subprocess.run(
                ['echo', command, '|', 'nc', 'localhost', '9999'],
                shell=True,
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                logger.debug(f"Sent command: {command}")
            else:
                logger.error(f"Failed to send command: {command}")
        except Exception as e:
            logger.error(f"Command error: {e}")
            
    def run_ai_loop(self):
        """Main AI control loop"""
        logger.info("Starting AI control loop")
        
        while self.running:
            try:
                # Read game state
                state = self.ocr_reader.read_game_state()
                if not state:
                    time.sleep(0.1)
                    continue
                    
                logger.debug(f"Game state: Health={state.health}, Armor={state.armor}")
                
                if self.use_mock_mvs:
                    # Use mock COBOL decisions
                    commands = self.mock_cobol_ai(state)
                else:
                    # Upload state to MVS
                    records = state.to_cobol_records()
                    # TODO: Implement actual FTP upload
                    
                    # Download commands from MVS
                    # TODO: Implement actual FTP download
                    commands = []
                    
                # Execute commands
                for cmd in commands:
                    self.send_command(cmd)
                    time.sleep(0.1)  # Small delay between commands
                    
                # Rate limit
                time.sleep(0.5)  # 2 Hz
                
            except Exception as e:
                logger.error(f"AI loop error: {e}")
                time.sleep(1)
                
    def mock_cobol_ai(self, state) -> list:
        """Simple AI logic mimicking COBOL program"""
        commands = []
        
        # Survival mode - low health
        if state.health < 30:
            logger.info("AI: Survival mode - retreating")
            commands.append("MOVE BACK 1")
            commands.append("TURN LEFT 45")
            
        # Combat mode - good health
        elif state.health > 70:
            logger.info("AI: Combat mode - advancing")
            commands.append("MOVE FORWARD 1")
            commands.append("SHOOT 2")
            
        # Exploration mode
        else:
            logger.info("AI: Exploration mode")
            commands.append("MOVE FORWARD 0.5")
            commands.append("TURN RIGHT 30")
            
        return commands
        
    def start(self):
        """Start the bridge"""
        self.running = True
        
        # Start AI loop in background
        ai_thread = threading.Thread(target=self.run_ai_loop, daemon=True)
        ai_thread.start()
        
        logger.info("DOOM-COBOL Bridge started!")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.running = False


def main():
    print("DOOM-COBOL Full System Startup")
    print("=" * 50)
    print()
    print("Prerequisites:")
    print("1. DOOM is running (chocolate-doom -iwad wads/doom1.wad -window)")
    print("2. COBOL interface is running (./run_local_cobol.sh)")
    print("3. DOOM is in gameplay (not in menu)")
    print()
    
    input("Press Enter when ready...")
    
    bridge = DoomCOBOLBridge(use_mock_mvs=True)
    bridge.start()


if __name__ == "__main__":
    main()