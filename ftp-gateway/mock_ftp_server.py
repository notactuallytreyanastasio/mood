#!/usr/bin/env python3
"""
Mock FTP Server simulating z/OS datasets for DOOM-COBOL
"""

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import os
import tempfile
import logging
import threading
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MVSDatasetHandler(FTPHandler):
    """FTP handler that simulates MVS dataset behavior"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datasets = {}
        self.dataset_dir = tempfile.mkdtemp(prefix='mvs_datasets_')
        logger.info(f"Dataset directory: {self.dataset_dir}")
        
        # Initialize standard datasets
        self._init_datasets()
        
    def _init_datasets(self):
        """Initialize DOOM datasets"""
        datasets = [
            'DOOM.GAMESTAT',
            'DOOM.COMMANDS', 
            'DOOM.ENTITIES',
            'DOOM.SOURCE',
            'DOOM.LOADLIB'
        ]
        
        for ds in datasets:
            path = os.path.join(self.dataset_dir, ds.replace('.', '_'))
            with open(path, 'wb') as f:
                # Write empty dataset with one blank record
                f.write(b' ' * 80)
            self.datasets[ds] = path
            
    def ftp_SITE(self, line):
        """Handle SITE commands for MVS emulation"""
        logger.info(f"SITE command: {line}")
        
        # Handle common MVS SITE commands
        if line.startswith('RECFM='):
            self.respond('200 SITE command accepted')
        elif line.startswith('LRECL='):
            self.respond('200 SITE command accepted')
        elif line.startswith('FILETYPE='):
            if 'JES' in line:
                self.job_mode = True
            self.respond('200 SITE command accepted')
        else:
            self.respond('202 SITE command not implemented')
            
    def ftp_STOR(self, file, mode='w'):
        """Store file - handle dataset names"""
        # Clean dataset name
        dataset = file.strip("'").upper()
        
        if dataset in self.datasets:
            # Store to dataset
            path = self.datasets[dataset]
            logger.info(f"Storing to dataset {dataset}")
            
            try:
                fd = self.run_as_current_user(self.fs.open, path, 'wb')
                self.data_channel.file_obj = fd
                self.data_channel.enable_receiving(self._current_type)
                
                # If it's a JCL job submission
                if dataset == 'DOOMAI' or dataset.endswith('.JCL'):
                    threading.Thread(target=self._process_job, args=(dataset,)).start()
                    
            except Exception as e:
                logger.error(f"STOR error: {e}")
                self.respond(f"550 {e}")
        else:
            # Regular file store
            super().ftp_STOR(file, mode)
            
    def ftp_RETR(self, file):
        """Retrieve file - handle dataset names"""
        # Clean dataset name
        dataset = file.strip("'").upper()
        
        if dataset in self.datasets:
            # Retrieve from dataset
            path = self.datasets[dataset]
            logger.info(f"Retrieving dataset {dataset}")
            
            try:
                fd = self.run_as_current_user(self.fs.open, path, 'rb')
                self.data_channel.file_obj = fd
                self.data_channel.enable_sending(self._current_type)
            except Exception as e:
                logger.error(f"RETR error: {e}")
                self.respond(f"550 {e}")
        else:
            # Regular file retrieve
            super().ftp_RETR(file)
            
    def _process_job(self, job_name):
        """Simulate job processing"""
        logger.info(f"Processing job {job_name}")
        time.sleep(1)  # Simulate processing
        
        # Run mock COBOL logic
        self._run_cobol_ai()
        
    def _run_cobol_ai(self):
        """Simulate COBOL AI processing"""
        try:
            # Read game state
            gamestat_path = self.datasets['DOOM.GAMESTAT']
            with open(gamestat_path, 'rb') as f:
                data = f.read()
                
            # Parse state (convert from EBCDIC)
            records = []
            for i in range(0, len(data), 80):
                record = data[i:i+80]
                if record and len(record) == 80:
                    try:
                        ascii_record = record.decode('cp037').strip()
                        if ascii_record:
                            records.append(ascii_record)
                    except:
                        pass
                        
            logger.info(f"COBOL AI: Processing {len(records)} state records")
            
            # Simple AI logic
            commands = []
            health = 100
            
            # Parse player record
            for record in records:
                if record.startswith('PLAYER'):
                    # Extract health (last 3 digits before armor)
                    health_str = record[-6:-3]
                    try:
                        health = int(health_str)
                    except:
                        pass
                        
            # Make decision based on health
            if health < 30:
                logger.info(f"COBOL AI: Low health ({health}) - retreating")
                commands.extend([
                    "MOVE BACK 020",
                    "TURN LEFT 090"
                ])
            elif health < 50:
                logger.info(f"COBOL AI: Medium health ({health}) - cautious")
                commands.extend([
                    "MOVE FORWARD 010",
                    "TURN RIGHT 045"
                ])
            else:
                logger.info(f"COBOL AI: Good health ({health}) - exploring")
                commands.extend([
                    "MOVE FORWARD 020",
                    "TURN RIGHT 030",
                    "SHOOT 001"
                ])
                
            # Write commands to dataset
            commands_path = self.datasets['DOOM.COMMANDS']
            with open(commands_path, 'wb') as f:
                for cmd in commands:
                    # Pad to 80 chars and convert to EBCDIC
                    padded = cmd.ljust(80)
                    ebcdic = padded.encode('cp037')
                    f.write(ebcdic)
                    
            logger.info(f"COBOL AI: Wrote {len(commands)} commands")
            
        except Exception as e:
            logger.error(f"COBOL AI error: {e}")


def start_mock_ftp_server(port=2121):
    """Start the mock FTP server"""
    # Create authorizer
    authorizer = DummyAuthorizer()
    authorizer.add_user("HERC01", "CUL8TR", ".", perm="elradfmw")
    
    # Create handler
    handler = MVSDatasetHandler
    handler.authorizer = authorizer
    
    # Create server
    server = FTPServer(("0.0.0.0", port), handler)
    server.max_cons = 256
    server.max_cons_per_ip = 5
    
    logger.info(f"Starting mock MVS FTP server on port {port}")
    logger.info("User: HERC01, Password: CUL8TR")
    
    # Start server
    server.serve_forever()


if __name__ == "__main__":
    start_mock_ftp_server()