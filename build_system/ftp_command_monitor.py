#!/usr/bin/env python3
"""
FTP Command Monitor Service for DOOM-COBOL Integration
Monitors DOOM.COMMANDS file written by DOOMAI2.COB and makes commands available via FTP
"""

import os
import time
import logging
import threading
import struct
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import ftplib
from io import BytesIO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DoomCommand:
    """Parsed DOOM command from COBOL"""
    record_type: str      # 8 chars
    action: str          # 8 chars (MOVE, TURN, SHOOT, USE, WEAPON, WAIT)
    direction: str       # 8 chars (FORWARD, BACK, LEFT, RIGHT)
    value: int          # 4 digits
    priority: int       # 1 digit
    reason: str         # 20 chars
    timestamp: float    # When parsed
    
    @classmethod
    def from_cobol_record(cls, record: bytes) -> Optional['DoomCommand']:
        """Parse 80-byte COBOL record into DoomCommand"""
        try:
            # Convert from EBCDIC if needed
            if record[0] > 127:  # Likely EBCDIC
                ascii_record = record.decode('cp037')
            else:
                ascii_record = record.decode('ascii')
                
            # Parse fixed-width fields according to DOOM-COMMAND-RECORD
            record_type = ascii_record[0:8].strip()
            action = ascii_record[8:16].strip()
            direction = ascii_record[16:24].strip()
            value = int(ascii_record[24:28])
            priority = int(ascii_record[28:29])
            reason = ascii_record[29:49].strip()
            
            # Validate record type
            if record_type != 'COMMAND':
                return None
                
            return cls(
                record_type=record_type,
                action=action,
                direction=direction,
                value=value,
                priority=priority,
                reason=reason,
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Failed to parse COBOL record: {e}")
            return None
            
    def to_ftp_format(self) -> str:
        """Convert to format suitable for FTP transfer"""
        # Format: ACTION DIRECTION VALUE PRIORITY REASON
        return f"{self.action:<8}{self.direction:<8}{self.value:04d} {self.priority} {self.reason:<20}"
        
    def to_cobol_interface_format(self) -> str:
        """Convert to format expected by COBOL interface on port 9999"""
        if self.action == 'MOVE':
            duration = self.value / 10.0  # Convert to seconds
            return f"MOVE {self.direction} {duration}"
        elif self.action == 'TURN':
            return f"TURN {self.direction} {self.value}"
        elif self.action == 'SHOOT':
            return f"SHOOT {self.value}"
        elif self.action == 'USE':
            return f"USE"
        elif self.action == 'WEAPON':
            return f"WEAPON {self.value}"
        elif self.action == 'WAIT':
            return f"WAIT {self.value / 10.0}"
        else:
            return f"{self.action} {self.direction} {self.value}"


class CommandFileMonitor:
    """Monitor DOOM.COMMANDS file for updates"""
    
    def __init__(self, commands_path: str = "cobol_datasets/DOOM.COMMANDS"):
        self.commands_path = Path(commands_path)
        self.last_mtime = 0
        self.last_size = 0
        self.commands_buffer: List[DoomCommand] = []
        self.lock = threading.Lock()
        
        # Create directory if needed
        self.commands_path.parent.mkdir(parents=True, exist_ok=True)
        
    def check_for_updates(self) -> bool:
        """Check if commands file has been updated"""
        if not self.commands_path.exists():
            return False
            
        try:
            stat = os.stat(self.commands_path)
            if stat.st_mtime > self.last_mtime or stat.st_size != self.last_size:
                self.last_mtime = stat.st_mtime
                self.last_size = stat.st_size
                return True
                
        except Exception as e:
            logger.error(f"Error checking file: {e}")
            
        return False
        
    def read_commands(self) -> List[DoomCommand]:
        """Read and parse commands from file"""
        commands = []
        
        try:
            with open(self.commands_path, 'rb') as f:
                # Read 80-byte records
                while True:
                    record = f.read(80)
                    if not record or len(record) < 80:
                        break
                        
                    cmd = DoomCommand.from_cobol_record(record)
                    if cmd:
                        commands.append(cmd)
                        logger.info(f"Parsed command: {cmd.action} {cmd.direction} {cmd.value}")
                        
        except Exception as e:
            logger.error(f"Error reading commands: {e}")
            
        return commands
        
    def get_pending_commands(self) -> List[DoomCommand]:
        """Get all pending commands"""
        with self.lock:
            commands = self.commands_buffer[:]
            self.commands_buffer = []
            return commands
            
    def monitor_loop(self):
        """Main monitoring loop"""
        logger.info(f"Monitoring {self.commands_path} for updates...")
        
        while True:
            try:
                if self.check_for_updates():
                    logger.info("Commands file updated, reading new commands...")
                    new_commands = self.read_commands()
                    
                    with self.lock:
                        self.commands_buffer.extend(new_commands)
                        
                    logger.info(f"Added {len(new_commands)} commands to buffer")
                    
                time.sleep(0.1)  # Check every 100ms
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(1)


class FTPCommandGateway:
    """FTP gateway for DOOM commands"""
    
    def __init__(self, monitor: CommandFileMonitor, ftp_host: str = 'localhost', 
                 ftp_port: int = 21, ftp_user: str = 'HERC01', ftp_pass: str = 'CUL8TR'):
        self.monitor = monitor
        self.ftp_host = ftp_host
        self.ftp_port = ftp_port
        self.ftp_user = ftp_user
        self.ftp_pass = ftp_pass
        self.connected = False
        self.ftp = None
        
    def connect(self) -> bool:
        """Connect to FTP server"""
        try:
            self.ftp = ftplib.FTP()
            self.ftp.connect(self.ftp_host, self.ftp_port, timeout=10)
            self.ftp.login(self.ftp_user, self.ftp_pass)
            self.ftp.voidcmd('TYPE I')  # Binary mode
            self.connected = True
            logger.info(f"Connected to FTP server at {self.ftp_host}")
            return True
            
        except Exception as e:
            logger.error(f"FTP connection failed: {e}")
            return False
            
    def upload_commands_dataset(self, commands: List[DoomCommand]) -> bool:
        """Upload commands to DOOM.COMMANDS.OUT dataset for FTP clients"""
        if not self.connected or not commands:
            return False
            
        try:
            # Convert commands to EBCDIC records
            data = BytesIO()
            for cmd in commands:
                # Format for FTP transfer
                record = cmd.to_ftp_format().ljust(80)
                ebcdic_record = record.encode('cp037')
                data.write(ebcdic_record)
                
            data.seek(0)
            
            # Upload to output dataset
            self.ftp.voidcmd('SITE RECFM=FB LRECL=80')
            self.ftp.storbinary("STOR 'DOOM.COMMANDS.OUT'", data)
            
            logger.info(f"Uploaded {len(commands)} commands to DOOM.COMMANDS.OUT")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload commands: {e}")
            return False
            
    def download_status_request(self) -> bool:
        """Check if FTP client requests command status"""
        if not self.connected:
            return False
            
        try:
            # Check for status request file
            files = self.ftp.nlst()
            return "'DOOM.STATUS.REQ'" in files
            
        except Exception as e:
            logger.error(f"Failed to check status: {e}")
            return False
            
    def clear_dataset(self, dataset_name: str) -> bool:
        """Clear a dataset"""
        try:
            self.ftp.delete(f"'{dataset_name}'")
            return True
        except:
            return False
            
    def gateway_loop(self):
        """Main FTP gateway loop"""
        if not self.connect():
            logger.error("Failed to start FTP gateway")
            return
            
        last_upload = 0
        upload_interval = 2.0  # Upload every 2 seconds if commands available
        
        while True:
            try:
                current_time = time.time()
                
                # Check for pending commands
                commands = self.monitor.get_pending_commands()
                
                # Upload if we have commands and enough time has passed
                if commands and (current_time - last_upload) > upload_interval:
                    if self.upload_commands_dataset(commands):
                        last_upload = current_time
                        
                # Check for status requests
                if self.download_status_request():
                    # Create status response
                    status = f"PENDING_COMMANDS: {len(commands)}\n"
                    status += f"LAST_UPLOAD: {datetime.fromtimestamp(last_upload)}\n"
                    
                    # Upload status
                    status_data = BytesIO(status.encode('cp037'))
                    self.ftp.storbinary("STOR 'DOOM.STATUS.OUT'", status_data)
                    self.clear_dataset('DOOM.STATUS.REQ')
                    
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Gateway loop error: {e}")
                time.sleep(1)
                
                # Try to reconnect
                if not self.connected:
                    self.connect()


class CommandStatusServer:
    """Simple HTTP server for command status"""
    
    def __init__(self, monitor: CommandFileMonitor, port: int = 8888):
        self.monitor = monitor
        self.port = port
        
    def serve(self):
        """Serve command status via HTTP"""
        import http.server
        import json
        
        class StatusHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/status':
                    with self.server.monitor.lock:
                        status = {
                            'pending_commands': len(self.server.monitor.commands_buffer),
                            'last_check': self.server.monitor.last_mtime,
                            'commands_file': str(self.server.monitor.commands_path)
                        }
                        
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(status, indent=2).encode())
                    
                elif self.path == '/commands':
                    commands = []
                    with self.server.monitor.lock:
                        for cmd in self.server.monitor.commands_buffer:
                            commands.append({
                                'action': cmd.action,
                                'direction': cmd.direction,
                                'value': cmd.value,
                                'priority': cmd.priority,
                                'reason': cmd.reason,
                                'timestamp': cmd.timestamp
                            })
                            
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(commands, indent=2).encode())
                    
                else:
                    self.send_response(404)
                    self.end_headers()
                    
        server = http.server.HTTPServer(('', self.port), StatusHandler)
        server.monitor = self.monitor
        
        logger.info(f"Status server running on port {self.port}")
        server.serve_forever()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DOOM-COBOL FTP Command Monitor')
    parser.add_argument('--commands-file', default='cobol_datasets/DOOM.COMMANDS',
                      help='Path to DOOM.COMMANDS file')
    parser.add_argument('--ftp-host', default='localhost',
                      help='FTP server host')
    parser.add_argument('--ftp-port', type=int, default=21,
                      help='FTP server port')
    parser.add_argument('--status-port', type=int, default=8888,
                      help='HTTP status server port')
    parser.add_argument('--no-ftp', action='store_true',
                      help='Disable FTP gateway')
    parser.add_argument('--no-status', action='store_true',
                      help='Disable HTTP status server')
    
    args = parser.parse_args()
    
    print("DOOM-COBOL FTP Command Monitor")
    print("=" * 50)
    print(f"Commands file: {args.commands_file}")
    print(f"FTP server: {args.ftp_host}:{args.ftp_port}")
    print(f"Status server: http://localhost:{args.status_port}")
    print()
    
    # Create monitor
    monitor = CommandFileMonitor(args.commands_file)
    
    # Start monitoring thread
    monitor_thread = threading.Thread(target=monitor.monitor_loop, daemon=True)
    monitor_thread.start()
    
    # Start FTP gateway if enabled
    if not args.no_ftp:
        gateway = FTPCommandGateway(monitor, args.ftp_host, args.ftp_port)
        gateway_thread = threading.Thread(target=gateway.gateway_loop, daemon=True)
        gateway_thread.start()
        
    # Start status server if enabled
    if not args.no_status:
        status_server = CommandStatusServer(monitor, args.status_port)
        status_thread = threading.Thread(target=status_server.serve, daemon=True)
        status_thread.start()
        
    print("Service running. Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        

if __name__ == "__main__":
    main()