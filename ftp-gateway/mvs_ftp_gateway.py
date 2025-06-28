#!/usr/bin/env python3
"""
MVS FTP Gateway for DOOM-COBOL Integration
Handles dataset transfers between z/OS and DOOM
"""

import os
import socket
import threading
import time
import logging
from datetime import datetime
from pathlib import Path
import struct

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MVSDataset:
    """Represents an MVS dataset with proper formatting"""
    
    def __init__(self, name, recfm='FB', lrecl=80, blksize=3200):
        self.name = name
        self.recfm = recfm
        self.lrecl = lrecl
        self.blksize = blksize
        self.records = []
        
    def add_record(self, data):
        """Add a record, padding/truncating to LRECL"""
        if isinstance(data, str):
            data = data.encode('cp037')  # EBCDIC
        
        # Pad or truncate to LRECL
        if len(data) < self.lrecl:
            data = data + b' ' * (self.lrecl - len(data))
        elif len(data) > self.lrecl:
            data = data[:self.lrecl]
            
        self.records.append(data)
        
    def to_bytes(self):
        """Convert to byte stream for FTP transfer"""
        if self.recfm == 'FB':
            # Fixed blocked - concatenate records
            return b''.join(self.records)
        else:
            # Variable format would need RDW headers
            raise NotImplementedError("Only FB supported")
            
    def from_bytes(self, data):
        """Parse byte stream into records"""
        self.records = []
        if self.recfm == 'FB':
            # Split into LRECL-sized chunks
            for i in range(0, len(data), self.lrecl):
                record = data[i:i+self.lrecl]
                if record:
                    self.records.append(record)


class MVSFTPGateway:
    """FTP gateway that understands MVS datasets"""
    
    def __init__(self, host='0.0.0.0', port=2121, data_dir='mvs_datasets'):
        self.host = host
        self.port = port
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Pre-defined datasets
        self.datasets = {
            'DOOM.GAMESTAT': MVSDataset('DOOM.GAMESTAT'),
            'DOOM.COMMANDS': MVSDataset('DOOM.COMMANDS'),
            'DOOM.AILOG': MVSDataset('DOOM.AILOG'),
        }
        
        # Active connections
        self.connections = {}
        
    def start(self):
        """Start FTP server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        
        logger.info(f"MVS FTP Gateway listening on {self.host}:{self.port}")
        
        try:
            while True:
                client, addr = server_socket.accept()
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client, addr)
                )
                thread.daemon = True
                thread.start()
        except KeyboardInterrupt:
            logger.info("Shutting down FTP gateway")
        finally:
            server_socket.close()
            
    def handle_client(self, client, addr):
        """Handle FTP client connection"""
        logger.info(f"Connection from {addr}")
        
        # Send welcome
        client.send(b"220 MVS FTP Gateway for DOOM-COBOL\r\n")
        
        conn_state = {
            'user': None,
            'auth': False,
            'type': 'A',  # ASCII default
            'mode': 'S',  # Stream
            'stru': 'F',  # File
            'pwd': '/',
            'data_conn': None,
            'passive': False,
        }
        
        self.connections[addr] = conn_state
        
        try:
            while True:
                data = client.recv(1024)
                if not data:
                    break
                    
                cmd_line = data.decode('ascii', errors='ignore').strip()
                logger.debug(f"Received: {cmd_line}")
                
                # Parse command
                parts = cmd_line.split(' ', 1)
                cmd = parts[0].upper()
                args = parts[1] if len(parts) > 1 else ''
                
                # Handle command
                response = self.handle_command(cmd, args, conn_state, client)
                if response:
                    client.send(response.encode('ascii') + b'\r\n')
                    
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            client.close()
            del self.connections[addr]
            logger.info(f"Disconnected {addr}")
            
    def handle_command(self, cmd, args, state, client):
        """Handle individual FTP commands"""
        
        if cmd == 'USER':
            state['user'] = args
            return "331 Password required"
            
        elif cmd == 'PASS':
            # Simple auth for demo
            if state['user'] == 'doom':
                state['auth'] = True
                return "230 User logged in"
            else:
                return "530 Login incorrect"
                
        elif cmd == 'QUIT':
            return "221 Goodbye"
            
        elif cmd == 'TYPE':
            if args.upper() == 'A':
                state['type'] = 'A'
                return "200 Type set to ASCII"
            elif args.upper() == 'I':
                state['type'] = 'I'
                return "200 Type set to Image (Binary)"
            else:
                return "504 Type not supported"
                
        elif cmd == 'MODE':
            if args.upper() == 'S':
                state['mode'] = 'S'
                return "200 Mode set to Stream"
            else:
                return "504 Mode not supported"
                
        elif cmd == 'PWD':
            return f'257 "{state["pwd"]}" is current directory'
            
        elif cmd == 'CWD' or cmd == 'CD':
            # Simulate directory structure
            if args in ['/', '/doom', '/doom/gamestate', '/doom/commands']:
                state['pwd'] = args
                return "250 Directory changed"
            else:
                return "550 Directory not found"
                
        elif cmd == 'LCD':
            # Local change directory (MVS dataset)
            # In JCL, this refers to the dataset
            return "250 Local directory changed"
            
        elif cmd == 'PASV':
            # Passive mode
            data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_socket.bind(('', 0))
            data_socket.listen(1)
            
            port = data_socket.getsockname()[1]
            state['data_conn'] = data_socket
            state['passive'] = True
            
            # Format: 227 (h1,h2,h3,h4,p1,p2)
            host_parts = self.host.split('.')
            if self.host == '0.0.0.0':
                host_parts = ['127', '0', '0', '1']
            p1 = port >> 8
            p2 = port & 0xFF
            
            return f"227 Entering Passive Mode ({','.join(host_parts)},{p1},{p2})"
            
        elif cmd == 'RETR' or cmd == 'GET':
            # Retrieve file/dataset
            if not state['auth']:
                return "530 Not logged in"
                
            # Map to our datasets
            if state['pwd'] == '/doom/gamestate':
                if args == 'GAMESTAT.CURRENT':
                    return self.send_gamestat(state, client)
            
            return "550 File not found"
            
        elif cmd == 'STOR' or cmd == 'PUT':
            # Store file/dataset
            if not state['auth']:
                return "530 Not logged in"
                
            # Map to our datasets
            if state['pwd'] == '/doom/commands':
                if args == 'COMMANDS.NEW':
                    return self.receive_commands(state, client)
                    
            return "550 Cannot store file"
            
        else:
            logger.warning(f"Unhandled command: {cmd}")
            return "502 Command not implemented"
            
    def send_gamestat(self, state, client):
        """Send current game state as MVS dataset"""
        # Get latest COBOL-formatted state
        gamestat_file = self.data_dir / "DOOM.GAMESTAT"
        
        if not gamestat_file.exists():
            # Create dummy state
            self.create_dummy_gamestat()
            
        # Read dataset
        dataset = self.datasets['DOOM.GAMESTAT']
        with open(gamestat_file, 'rb') as f:
            dataset.from_bytes(f.read())
            
        # Send via data connection
        client.send(b"150 Opening data connection\r\n")
        
        if state['passive']:
            data_conn, _ = state['data_conn'].accept()
        else:
            # Active mode not implemented
            return "425 Cannot open data connection"
            
        try:
            # Send dataset records
            data = dataset.to_bytes()
            
            # Convert to EBCDIC if in ASCII mode
            if state['type'] == 'A':
                # MVS FTP expects EBCDIC
                data = data.decode('ascii', errors='ignore').encode('cp037')
                
            data_conn.send(data)
            data_conn.close()
            
            logger.info(f"Sent {len(dataset.records)} records")
            return "226 Transfer complete"
            
        except Exception as e:
            logger.error(f"Transfer error: {e}")
            return "426 Transfer aborted"
            
    def receive_commands(self, state, client):
        """Receive command dataset from COBOL"""
        client.send(b"150 Opening data connection\r\n")
        
        if state['passive']:
            data_conn, _ = state['data_conn'].accept()
        else:
            return "425 Cannot open data connection"
            
        try:
            # Receive data
            data = b''
            while True:
                chunk = data_conn.recv(4096)
                if not chunk:
                    break
                data += chunk
                
            data_conn.close()
            
            # Parse as MVS dataset
            dataset = MVSDataset('DOOM.COMMANDS')
            
            # Convert from EBCDIC if needed
            if state['type'] == 'A':
                # Convert EBCDIC to ASCII for processing
                data = data.decode('cp037').encode('ascii')
                
            dataset.from_bytes(data)
            
            # Save and process
            commands_file = self.data_dir / "DOOM.COMMANDS"
            with open(commands_file, 'wb') as f:
                f.write(dataset.to_bytes())
                
            # Also save ASCII version for processing
            ascii_file = self.data_dir / "DOOM.COMMANDS.ASCII"
            with open(ascii_file, 'w') as f:
                for record in dataset.records:
                    # Decode from EBCDIC
                    text = record.decode('cp037', errors='ignore')
                    f.write(text + '\n')
                    
            logger.info(f"Received {len(dataset.records)} command records")
            
            # Process commands
            self.process_commands(dataset)
            
            return "226 Transfer complete"
            
        except Exception as e:
            logger.error(f"Receive error: {e}")
            return "426 Transfer aborted"
            
    def create_dummy_gamestat(self):
        """Create dummy game state for testing"""
        dataset = MVSDataset('DOOM.GAMESTAT')
        
        # Add sample records
        dataset.add_record("STATE   00001234011202501010000000000000000000000000000000000000000000000000000")
        dataset.add_record("PLAYER  +0001024+0001024+0000000+090075050A        0000000000000000000000000000")
        dataset.add_record("AMMO    0050002001000040200000000000000000000000000000000000000000000000000000")
        dataset.add_record("ENEMY   09100+0001200+0001100002560000        000000000000000000000000000000000")
        
        # Save to file
        gamestat_file = self.data_dir / "DOOM.GAMESTAT"
        with open(gamestat_file, 'wb') as f:
            f.write(dataset.to_bytes())
            
    def process_commands(self, dataset):
        """Process received COBOL commands"""
        commands = []
        
        for record in dataset.records:
            # Decode EBCDIC record
            text = record.decode('cp037', errors='ignore')
            
            # Parse DOOM-COMMAND-RECORD
            if text[:8].strip() == 'COMMAND':
                cmd = {
                    'action': text[8:16].strip(),
                    'direction': text[16:24].strip(),
                    'value': int(text[24:28]),
                    'priority': int(text[28:29]),
                    'reason': text[29:49].strip()
                }
                commands.append(cmd)
                logger.info(f"Command: {cmd['action']} {cmd['direction']} {cmd['value']}")
                
        # Write to action queue
        action_file = self.data_dir / "pending_actions.txt"
        with open(action_file, 'w') as f:
            for cmd in commands:
                # Convert to DOOM input format
                if cmd['action'] == 'MOVE':
                    f.write(f"MOVE {cmd['direction']} {cmd['value']/10}\n")
                elif cmd['action'] == 'TURN':
                    f.write(f"TURN {cmd['direction']} {cmd['value']}\n")
                elif cmd['action'] == 'SHOOT':
                    f.write(f"SHOOT {cmd['value']}\n")
                elif cmd['action'] == 'WAIT':
                    f.write(f"WAIT {cmd['value']/10}\n")
                    
        logger.info(f"Processed {len(commands)} commands")


def main():
    """Run MVS FTP Gateway"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MVS FTP Gateway for DOOM-COBOL')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=2121, help='Port to listen on')
    parser.add_argument('--data-dir', default='mvs_datasets', help='Dataset directory')
    
    args = parser.parse_args()
    
    gateway = MVSFTPGateway(args.host, args.port, args.data_dir)
    
    print(f"""
╔══════════════════════════════════════════════════════╗
║          MVS FTP Gateway for DOOM-COBOL              ║
╚══════════════════════════════════════════════════════╝

FTP Server: {args.host}:{args.port}
Dataset Directory: {args.data_dir}

Use this in your JCL:
  open {args.host} {args.port}
  user doom doomguy

Datasets available:
  /doom/gamestate/GAMESTAT.CURRENT - Current game state
  /doom/commands/COMMANDS.NEW      - Command upload

Press Ctrl+C to stop
""")
    
    try:
        gateway.start()
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()