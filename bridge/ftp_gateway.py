#!/usr/bin/env python3
"""
FTP Gateway for DOOM-COBOL Integration
Handles dataset transfers between DOOM and MVS
"""

import ftplib
import time
import logging
import threading
from io import BytesIO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MVSDatasetManager:
    """Manages MVS dataset operations via FTP"""
    
    def __init__(self, host='localhost', user='HERC01', password='CUL8TR', port=21):
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.ftp = None
        self.connected = False
        
    def connect(self):
        """Connect to MVS FTP server"""
        try:
            self.ftp = ftplib.FTP()
            self.ftp.connect(self.host, self.port, timeout=10)
            self.ftp.login(self.user, self.password)
            
            # Set to binary mode
            self.ftp.voidcmd('TYPE I')
            
            # Set record format for datasets
            self.ftp.voidcmd('SITE RECFM=FB LRECL=80')
            
            self.connected = True
            logger.info(f"Connected to MVS at {self.host}")
            return True
            
        except Exception as e:
            logger.error(f"FTP connection failed: {e}")
            return False
            
    def upload_game_state(self, state_records):
        """Upload game state to DOOM.GAMESTAT dataset"""
        if not self.connected:
            return False
            
        try:
            # Convert records to EBCDIC
            data = BytesIO()
            for record in state_records:
                # Pad to 80 characters and convert to EBCDIC
                padded = record.ljust(80)
                ebcdic_record = padded.encode('cp037')
                data.write(ebcdic_record)
                
            data.seek(0)
            
            # Upload to dataset
            self.ftp.storbinary("STOR 'DOOM.GAMESTAT'", data)
            logger.info(f"Uploaded {len(state_records)} records to DOOM.GAMESTAT")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload game state: {e}")
            return False
            
    def download_commands(self):
        """Download commands from DOOM.COMMANDS dataset"""
        if not self.connected:
            return []
            
        try:
            # Download dataset
            data = BytesIO()
            self.ftp.retrbinary("RETR 'DOOM.COMMANDS'", data.write)
            
            # Parse EBCDIC records
            data.seek(0)
            raw_data = data.read()
            commands = []
            
            # Process 80-byte records
            for i in range(0, len(raw_data), 80):
                record = raw_data[i:i+80]
                if record:
                    # Convert from EBCDIC to ASCII
                    ascii_record = record.decode('cp037').strip()
                    if ascii_record:
                        commands.append(ascii_record)
                        
            logger.info(f"Downloaded {len(commands)} commands from DOOM.COMMANDS")
            return commands
            
        except Exception as e:
            logger.error(f"Failed to download commands: {e}")
            return []
            
    def submit_job(self, jcl_name='DOOMAI'):
        """Submit JCL job to process game state"""
        if not self.connected:
            return None
            
        try:
            # Switch to JES mode
            self.ftp.voidcmd('SITE FILETYPE=JES')
            
            # Submit the job
            with open(f'jcl/{jcl_name}.JCL', 'rb') as f:
                response = self.ftp.storlines(f"STOR {jcl_name}", f)
                
            # Extract job ID from response
            if 'JOB' in response:
                job_id = response.split()[1]
                logger.info(f"Submitted job {job_id}")
                return job_id
            else:
                logger.warning(f"Job submitted but no ID returned: {response}")
                return "UNKNOWN"
                
        except Exception as e:
            logger.error(f"Failed to submit job: {e}")
            return None
            
    def check_job_status(self, job_id):
        """Check if job has completed"""
        # For now, just wait a fixed time
        # Real implementation would check JES spool
        return True
        
    def clear_dataset(self, dataset_name):
        """Clear a dataset by deleting and reallocating"""
        try:
            # Delete if exists
            try:
                self.ftp.delete(f"'{dataset_name}'")
            except:
                pass  # Dataset might not exist
                
            # Allocate new dataset
            self.ftp.voidcmd(f"SITE RECFM=FB LRECL=80 BLKSIZE=3200")
            self.ftp.voidcmd(f"SITE TRACKS PRIMARY=5 SECONDARY=5")
            
            # Create empty dataset
            empty_data = BytesIO(b' ' * 80)  # One blank record
            self.ftp.storbinary(f"STOR '{dataset_name}'", empty_data)
            
            logger.info(f"Cleared dataset {dataset_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear dataset: {e}")
            return False


class DoomFTPBridge:
    """Main bridge between DOOM and MVS via FTP"""
    
    def __init__(self):
        self.mvs = MVSDatasetManager()
        self.running = False
        self.state_file = '/tmp/doom_state.dat'
        self.command_port = 9999  # COBOL interface port
        
    def start(self):
        """Start the bridge"""
        logger.info("Starting DOOM-FTP Bridge")
        
        # Connect to MVS
        if not self.mvs.connect():
            logger.error("Failed to connect to MVS")
            return False
            
        # Clear datasets
        self.mvs.clear_dataset('DOOM.GAMESTAT')
        self.mvs.clear_dataset('DOOM.COMMANDS')
        
        self.running = True
        
        # Start processing loop
        thread = threading.Thread(target=self._process_loop, daemon=True)
        thread.start()
        
        return True
        
    def _process_loop(self):
        """Main processing loop"""
        last_state_time = 0
        
        while self.running:
            try:
                # Check for new game state
                import os
                if os.path.exists(self.state_file):
                    stat = os.stat(self.state_file)
                    if stat.st_mtime > last_state_time:
                        # New state available
                        last_state_time = stat.st_mtime
                        self._process_state_update()
                        
                time.sleep(0.5)  # Check every 500ms
                
            except Exception as e:
                logger.error(f"Process loop error: {e}")
                time.sleep(1)
                
    def _process_state_update(self):
        """Process new game state"""
        logger.info("Processing new game state")
        
        # Read state file
        try:
            with open(self.state_file, 'r') as f:
                state_records = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.error(f"Failed to read state file: {e}")
            return
            
        # Upload to MVS
        if not self.mvs.upload_game_state(state_records):
            return
            
        # Submit COBOL job
        job_id = self.mvs.submit_job('DOOMAI')
        if not job_id:
            return
            
        # Wait for job to complete
        logger.info("Waiting for COBOL processing...")
        time.sleep(2)  # Simple wait for now
        
        # Download commands
        commands = self.mvs.download_commands()
        if not commands:
            logger.warning("No commands received from COBOL")
            return
            
        # Execute commands
        self._execute_commands(commands)
        
        # Clear commands dataset for next cycle
        self.mvs.clear_dataset('DOOM.COMMANDS')
        
    def _execute_commands(self, commands):
        """Send commands to DOOM via COBOL interface"""
        import socket
        
        for cmd in commands:
            try:
                # Parse COBOL command format
                # Example: "MOVE FORWARD 002" or "TURN RIGHT 045"
                parts = cmd.split()
                if len(parts) >= 2:
                    action = parts[0]
                    param1 = parts[1]
                    param2 = parts[2] if len(parts) > 2 else ""
                    
                    # Build command for COBOL interface
                    if action == "MOVE":
                        duration = int(param2) / 10.0 if param2 else 0.5
                        command = f"MOVE {param1} {duration}"
                    elif action == "TURN":
                        degrees = int(param2) if param2 else 45
                        command = f"TURN {param1} {degrees}"
                    elif action == "SHOOT":
                        count = int(param1) if param1.isdigit() else 1
                        command = f"SHOOT {count}"
                    else:
                        command = cmd
                        
                    # Send to COBOL interface
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect(('localhost', self.command_port))
                    sock.send(f"{command}\n".encode())
                    response = sock.recv(1024)
                    sock.close()
                    
                    logger.info(f"Executed: {command} -> {response.decode().strip()}")
                    
            except Exception as e:
                logger.error(f"Failed to execute command '{cmd}': {e}")
                
    def stop(self):
        """Stop the bridge"""
        self.running = False
        if self.mvs.ftp:
            self.mvs.ftp.quit()
            

def main():
    """Run the FTP bridge"""
    print("DOOM-MVS FTP Bridge")
    print("=" * 50)
    print()
    print("This bridge:")
    print("1. Monitors /tmp/doom_state.dat for game state")
    print("2. Uploads state to MVS dataset DOOM.GAMESTAT")
    print("3. Submits COBOL job DOOMAI")
    print("4. Downloads commands from DOOM.COMMANDS")
    print("5. Sends commands to COBOL interface on port 9999")
    print()
    
    bridge = DoomFTPBridge()
    
    if not bridge.start():
        print("Failed to start bridge!")
        return
        
    print("Bridge running. Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping bridge...")
        bridge.stop()
        

if __name__ == "__main__":
    main()