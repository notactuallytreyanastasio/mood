#!/usr/bin/env python3
"""
COBOL Command Interface for DOOM
Provides a simple TCP interface to submit DOOM commands via COBOL/JCL
"""

import socket
import threading
import ftplib
import time
import json
import logging
import os
from dataclasses import dataclass
from typing import List, Optional
import structlog

# Import mock MVS if available
try:
    from mock_mvs import mock_mvs
    MOCK_MODE = True
except ImportError:
    MOCK_MODE = False

# Import direct DOOM controller if available
try:
    from direct_doom import doom_controller
    DIRECT_CONTROL = True
except ImportError:
    DIRECT_CONTROL = False

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@dataclass
class DoomCommand:
    """High-level DOOM command"""
    action: str  # MOVE, TURN, SHOOT, USE, WEAPON
    direction: Optional[str] = None  # FORWARD, BACK, LEFT, RIGHT
    value: Optional[int] = None  # Degrees for TURN, weapon number, etc.
    duration: Optional[float] = None  # Seconds for MOVE


class COBOLInterface:
    """TCP server that accepts high-level commands and submits them to MVS"""
    
    def __init__(self, port=9999):
        self.port = port
        self.mvs_host = os.environ.get('MVS_HOST', 'mainframe')
        self.mvs_user = os.environ.get('MVS_USER', 'HERC01')
        self.mvs_pass = os.environ.get('MVS_PASS', 'CUL8TR')
        self.server_socket = None
        self.running = False
        
    def start(self):
        """Start the TCP server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(5)
        self.running = True
        
        logger.info("COBOL interface started", port=self.port, mock_mode=MOCK_MODE, direct_control=DIRECT_CONTROL)
        
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                logger.info("Client connected", address=address)
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    logger.error("Server error", error=str(e))
                    
    def handle_client(self, client_socket, address):
        """Handle individual client connection"""
        try:
            while True:
                # Receive command (newline terminated)
                data = client_socket.recv(1024)
                if not data:
                    break
                    
                command_str = data.decode('utf-8').strip()
                logger.info("Received command", command=command_str, from_address=address)
                
                # Parse and execute command
                try:
                    response = self.process_command(command_str)
                    client_socket.send(f"{response}\n".encode('utf-8'))
                except Exception as e:
                    error_msg = f"ERROR: {str(e)}"
                    client_socket.send(f"{error_msg}\n".encode('utf-8'))
                    logger.error("Command processing failed", 
                               command=command_str, error=str(e))
                    
        except Exception as e:
            logger.error("Client handler error", address=address, error=str(e))
        finally:
            client_socket.close()
            logger.info("Client disconnected", address=address)
            
    def process_command(self, command_str: str) -> str:
        """Process a command string and submit to MVS"""
        # Parse command format: ACTION [PARAMS]
        parts = command_str.upper().split()
        if not parts:
            return "ERROR: Empty command"
            
        action = parts[0]
        
        # Create DOOM command based on action
        if action == "MOVE":
            # MOVE FORWARD|BACK|LEFT|RIGHT [duration]
            if len(parts) < 2:
                return "ERROR: MOVE requires direction"
            direction = parts[1]
            duration = float(parts[2]) if len(parts) > 2 else 0.5
            return self.submit_move_command(direction, duration)
            
        elif action == "TURN":
            # TURN LEFT|RIGHT [degrees]
            if len(parts) < 2:
                return "ERROR: TURN requires direction"
            direction = parts[1]
            degrees = int(parts[2]) if len(parts) > 2 else 45
            return self.submit_turn_command(direction, degrees)
            
        elif action == "SHOOT":
            # SHOOT [count]
            count = int(parts[1]) if len(parts) > 1 else 1
            return self.submit_shoot_command(count)
            
        elif action == "USE":
            # USE (opens doors, activates switches)
            return self.submit_use_command()
            
        elif action == "WEAPON":
            # WEAPON [number]
            if len(parts) < 2:
                return "ERROR: WEAPON requires number (1-7)"
            weapon_num = int(parts[1])
            return self.submit_weapon_command(weapon_num)
            
        elif action == "ESCAPE" or action == "ESC":
            # ESCAPE - Press ESC key (for menus)
            return self.submit_escape_command()
            
        elif action == "ENTER":
            # ENTER - Press Enter key (for menus) 
            return self.submit_enter_command()
            
        elif action == "RUN":
            # RUN jobname - Submit custom JCL
            if len(parts) < 2:
                return "ERROR: RUN requires job name"
            job_name = parts[1]
            return self.submit_jcl_job(job_name)
            
        elif action == "STATUS":
            # STATUS - Get current game state
            return self.get_game_status()
            
        else:
            return f"ERROR: Unknown command: {action}"
            
    def submit_move_command(self, direction: str, duration: float) -> str:
        """Submit movement command to MVS"""
        # Direct control if available
        if DIRECT_CONTROL:
            doom_controller.add_move_command(direction, duration)
            
        # Generate COBOL record for movement
        key_map = {
            'FORWARD': 'W',
            'BACK': 'S',
            'LEFT': 'A',
            'RIGHT': 'D'
        }
        
        if direction not in key_map:
            return f"ERROR: Invalid direction: {direction}"
            
        # Create command records (press, wait, release)
        commands = [
            f"KP{key_map[direction]}   +000+000",  # Key press
            f"WAIT {int(duration * 1000):04d}",    # Wait in ms
            f"KR{key_map[direction]}   +000+000"   # Key release
        ]
        
        result = self.upload_commands(commands)
        if DIRECT_CONTROL and "OK" in result:
            return result + " + DIRECT"
        return result
        
    def submit_turn_command(self, direction: str, degrees: int) -> str:
        """Submit turn command to MVS"""
        # Direct control if available
        if DIRECT_CONTROL:
            doom_controller.add_turn_command(direction, degrees)
            
        # Calculate mouse movement for degrees
        # Approximate: 10 pixels = 1 degree
        pixels = degrees * 10
        
        if direction == 'LEFT':
            mouse_x = -pixels
        elif direction == 'RIGHT':
            mouse_x = pixels
        else:
            return f"ERROR: Invalid turn direction: {direction}"
            
        commands = [
            f"MPMOVE{mouse_x:+04d}+000"  # Mouse move
        ]
        
        result = self.upload_commands(commands)
        if DIRECT_CONTROL and "OK" in result:
            return result + " + DIRECT"
        return result
        
    def submit_shoot_command(self, count: int) -> str:
        """Submit shoot command to MVS"""
        # Direct control if available
        if DIRECT_CONTROL:
            doom_controller.add_shoot_command(count)
            
        commands = []
        for _ in range(count):
            commands.extend([
                "MPBTN1+000+000",      # Mouse button press
                "WAIT 0100",           # Wait 100ms
                "MRBTN1+000+000",      # Mouse button release
                "WAIT 0200"            # Wait between shots
            ])
            
        result = self.upload_commands(commands)
        if DIRECT_CONTROL and "OK" in result:
            return result + " + DIRECT"
        return result
        
    def submit_use_command(self) -> str:
        """Submit use command to MVS"""
        # Direct control if available
        if DIRECT_CONTROL:
            doom_controller.add_use_command()
            
        commands = [
            "KPE   +000+000",  # Press E (use key)
            "WAIT 0100",
            "KRE   +000+000"   # Release E
        ]
        
        result = self.upload_commands(commands)
        if DIRECT_CONTROL and "OK" in result:
            return result + " + DIRECT"
        return result
        
    def submit_weapon_command(self, weapon_num: int) -> str:
        """Submit weapon switch command to MVS"""
        if weapon_num < 1 or weapon_num > 7:
            return "ERROR: Weapon number must be 1-7"
            
        commands = [
            f"KP{weapon_num}   +000+000",  # Press number key
            "WAIT 0050",
            f"KR{weapon_num}   +000+000"   # Release number key
        ]
        
        return self.upload_commands(commands)
        
    def submit_escape_command(self) -> str:
        """Submit ESC key command to MVS"""
        # Direct control if available
        if DIRECT_CONTROL:
            doom_controller.add_escape_command()
            
        commands = [
            "KPESC +000+000",  # Press ESC
            "WAIT 0100",
            "KRESC +000+000"   # Release ESC
        ]
        
        result = self.upload_commands(commands)
        if DIRECT_CONTROL and "OK" in result:
            return result + " + DIRECT"
        return result
        
    def submit_enter_command(self) -> str:
        """Submit Enter key command to MVS"""
        # Direct control if available
        if DIRECT_CONTROL:
            doom_controller.add_enter_command()
            
        commands = [
            "KPENT +000+000",  # Press Enter
            "WAIT 0100",
            "KRENT +000+000"   # Release Enter
        ]
        
        result = self.upload_commands(commands)
        if DIRECT_CONTROL and "OK" in result:
            return result + " + DIRECT"
        return result
        
    def upload_commands(self, commands: List[str]) -> str:
        """Upload command records to MVS DOOM.COMMANDS dataset"""
        if MOCK_MODE:
            # Use mock MVS
            try:
                for cmd in commands:
                    record = cmd.ljust(80).encode('cp037')
                    mock_mvs.datasets['DOOM.COMMANDS'].records.append(record)
                return f"OK: Submitted {len(commands)} commands (MOCK)"
            except Exception as e:
                return f"ERROR: Mock MVS failed - {str(e)}"
        else:
            try:
                # Connect to MVS FTP
                ftp = ftplib.FTP(self.mvs_host)
                ftp.login(self.mvs_user, self.mvs_pass)
                ftp.sendcmd('SITE RECFM=FB LRECL=80')
                
                # Format commands as 80-byte EBCDIC records
                data = b''
                for cmd in commands:
                    # Pad to 80 characters and convert to EBCDIC
                    record = cmd.ljust(80)
                    data += record.encode('cp037')
                    
                # Upload to DOOM.COMMANDS dataset
                ftp.storbinary('STOR DOOM.COMMANDS', data)
                ftp.quit()
                
                return f"OK: Submitted {len(commands)} commands"
                
            except Exception as e:
                return f"ERROR: FTP failed - {str(e)}"
            
    def submit_jcl_job(self, job_name: str) -> str:
        """Submit a pre-defined JCL job"""
        try:
            # Read JCL template
            template_path = f"/templates/{job_name}.jcl"
            if not os.path.exists(template_path):
                return f"ERROR: Job template not found: {job_name}"
                
            with open(template_path, 'r') as f:
                jcl_content = f.read()
                
            # Submit via FTP to INTRDR
            ftp = ftplib.FTP(self.mvs_host)
            ftp.login(self.mvs_user, self.mvs_pass)
            ftp.sendcmd('SITE FILETYPE=JES')
            
            # Convert to EBCDIC and submit
            jcl_data = jcl_content.encode('cp037')
            response = ftp.storbinary('STOR job.jcl', jcl_data)
            
            ftp.quit()
            
            # Extract job ID from response
            if 'JOB' in response:
                job_id = response.split()[1]
                return f"OK: Submitted job {job_id}"
            else:
                return f"OK: Job submitted - {response}"
                
        except Exception as e:
            return f"ERROR: Job submission failed - {str(e)}"
            
    def get_game_status(self) -> str:
        """Retrieve current game state from MVS"""
        if MOCK_MODE:
            # Use mock MVS
            try:
                if mock_mvs.datasets['DOOM.STATE'].records:
                    record = mock_mvs.datasets['DOOM.STATE'].records[0].decode('cp037').strip()
                    tick = record[0:9]
                    player_x = record[9:19]
                    player_y = record[19:29]
                    health = record[39:42]
                    return f"OK: Tick={tick} X={player_x} Y={player_y} Health={health} (MOCK)"
                else:
                    return "ERROR: No game state available (MOCK)"
            except Exception as e:
                return f"ERROR: Mock status failed - {str(e)}"
        else:
            try:
                ftp = ftplib.FTP(self.mvs_host)
                ftp.login(self.mvs_user, self.mvs_pass)
                
                # Download DOOM.STATE dataset
                data = []
                ftp.retrbinary('RETR DOOM.STATE', data.append)
                ftp.quit()
                
                if data:
                    # Parse EBCDIC record
                    record = b''.join(data).decode('cp037').strip()
                    # Extract key fields (based on COBOL layout)
                    tick = record[0:9]
                    player_x = record[9:19]
                    player_y = record[19:29]
                    health = record[39:42]
                    
                    return f"OK: Tick={tick} X={player_x} Y={player_y} Health={health}"
                else:
                    return "ERROR: No game state available"
                    
            except Exception as e:
                return f"ERROR: Status retrieval failed - {str(e)}"
            
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()


def main():
    """Main entry point"""
    # Get configuration from environment
    port = int(os.environ.get('COMMAND_PORT', '9999'))
    
    # Create and start interface
    interface = COBOLInterface(port)
    
    try:
        logger.info("Starting COBOL command interface", port=port)
        interface.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error("Fatal error", error=str(e))
    finally:
        interface.stop()
        logger.info("COBOL interface stopped")


if __name__ == '__main__':
    main()