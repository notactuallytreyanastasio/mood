#!/usr/bin/env python3
"""
FTP Action Reader - Reads COBOL commands from FTP gateway
Monitors for new commands and queues them for processing
"""

import os
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional
import threading
import queue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class COBOLCommandParser:
    """Parse COBOL DOOM-COMMAND-RECORD format"""
    
    @staticmethod
    def parse_record(record: str) -> Optional[Dict]:
        """Parse 80-byte COBOL command record"""
        if len(record) < 80:
            record = record.ljust(80)
            
        # DOOM-COMMAND-RECORD structure:
        # 01-08: CMD-RECORD-TYPE (COMMAND)
        # 09-16: CMD-ACTION (MOVE/TURN/SHOOT/USE/WEAPON/WAIT)
        # 17-24: CMD-DIRECTION (FORWARD/BACK/LEFT/RIGHT)
        # 25-28: CMD-VALUE (9999)
        # 29-29: CMD-PRIORITY (9)
        # 30-49: CMD-REASON (X(20))
        # 50-80: FILLER
        
        record_type = record[0:8].strip()
        if record_type != 'COMMAND':
            return None
            
        command = {
            'type': record_type,
            'action': record[8:16].strip(),
            'direction': record[16:24].strip(),
            'value': int(record[24:28]) if record[24:28].strip().isdigit() else 0,
            'priority': int(record[28:29]) if record[28:29].isdigit() else 5,
            'reason': record[29:49].strip(),
            'raw': record
        }
        
        return command
        
    @staticmethod
    def command_to_doom_format(cmd: Dict) -> str:
        """Convert COBOL command to DOOM input format"""
        action = cmd['action']
        
        if action == 'MOVE':
            # Convert value to seconds (COBOL uses centiseconds)
            duration = cmd['value'] / 10.0
            return f"MOVE {cmd['direction']} {duration}"
            
        elif action == 'TURN':
            # Value is in degrees
            return f"TURN {cmd['direction']} {cmd['value']}"
            
        elif action == 'SHOOT':
            # Value is repeat count
            return f"SHOOT {cmd['value']}"
            
        elif action == 'USE':
            return "USE"
            
        elif action == 'WEAPON':
            # Value is weapon number
            return f"WEAPON {cmd['value']}"
            
        elif action == 'WAIT':
            # Convert to seconds
            duration = cmd['value'] / 10.0
            return f"WAIT {duration}"
            
        else:
            logger.warning(f"Unknown action: {action}")
            return f"# Unknown: {action}"


class FTPActionReader:
    """Monitors FTP gateway for new COBOL commands"""
    
    def __init__(self, watch_dir="mvs_datasets", poll_interval=1.0):
        self.watch_dir = Path(watch_dir)
        self.poll_interval = poll_interval
        self.command_queue = queue.Queue()
        self.processed_files = set()
        self.running = False
        
        # Files to monitor
        self.command_files = [
            "DOOM.COMMANDS",
            "DOOM.COMMANDS.ASCII",
            "pending_actions.txt"
        ]
        
    def start(self):
        """Start monitoring for commands"""
        self.running = True
        monitor_thread = threading.Thread(target=self._monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        logger.info(f"Started monitoring {self.watch_dir}")
        
    def stop(self):
        """Stop monitoring"""
        self.running = False
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Check each command file
                for filename in self.command_files:
                    filepath = self.watch_dir / filename
                    if filepath.exists():
                        # Check if file is new or modified
                        file_key = f"{filename}:{filepath.stat().st_mtime}"
                        if file_key not in self.processed_files:
                            self._process_file(filepath)
                            self.processed_files.add(file_key)
                            
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                
            time.sleep(self.poll_interval)
            
    def _process_file(self, filepath: Path):
        """Process a command file"""
        logger.info(f"Processing {filepath.name}")
        
        try:
            if filepath.name == "pending_actions.txt":
                # Already in DOOM format
                with open(filepath, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            self.command_queue.put({
                                'source': 'pending_actions',
                                'command': line,
                                'timestamp': time.time()
                            })
                            
            elif filepath.name.endswith('.ASCII'):
                # ASCII version of COBOL dataset
                with open(filepath, 'r') as f:
                    for line in f:
                        cmd = COBOLCommandParser.parse_record(line.rstrip('\n'))
                        if cmd:
                            doom_cmd = COBOLCommandParser.command_to_doom_format(cmd)
                            self.command_queue.put({
                                'source': 'cobol_ascii',
                                'command': doom_cmd,
                                'cobol': cmd,
                                'timestamp': time.time()
                            })
                            
            else:
                # EBCDIC COBOL dataset
                with open(filepath, 'rb') as f:
                    data = f.read()
                    
                # Process 80-byte records
                for i in range(0, len(data), 80):
                    record = data[i:i+80]
                    if len(record) == 80:
                        # Convert from EBCDIC
                        try:
                            text = record.decode('cp037')
                            cmd = COBOLCommandParser.parse_record(text)
                            if cmd:
                                doom_cmd = COBOLCommandParser.command_to_doom_format(cmd)
                                self.command_queue.put({
                                    'source': 'cobol_ebcdic',
                                    'command': doom_cmd,
                                    'cobol': cmd,
                                    'timestamp': time.time()
                                })
                        except Exception as e:
                            logger.error(f"EBCDIC decode error: {e}")
                            
            logger.info(f"Queued {self.command_queue.qsize()} commands")
            
        except Exception as e:
            logger.error(f"Error processing {filepath.name}: {e}")
            
    def get_commands(self, timeout=0.1) -> List[Dict]:
        """Get all pending commands"""
        commands = []
        
        try:
            while True:
                cmd = self.command_queue.get(timeout=timeout)
                commands.append(cmd)
        except queue.Empty:
            pass
            
        return commands
        
    def get_latest_command(self) -> Optional[Dict]:
        """Get the most recent command"""
        commands = self.get_commands()
        return commands[-1] if commands else None


def test_parser():
    """Test COBOL command parsing"""
    test_records = [
        "COMMAND MOVE    FORWARD 00209SURVIVAL RETREAT                               ",
        "COMMAND TURN    RIGHT   00303SECONDARY ACTION                               ",
        "COMMAND SHOOT           00015COMBAT ENGAGEMENT                              ",
        "COMMAND WAIT            00107NO ACTION DETERMINED                           ",
    ]
    
    print("Testing COBOL command parser:")
    print("=" * 60)
    
    for record in test_records:
        cmd = COBOLCommandParser.parse_record(record)
        if cmd:
            doom_fmt = COBOLCommandParser.command_to_doom_format(cmd)
            print(f"COBOL: {record[:49]}")
            print(f"Parsed: {cmd['action']} {cmd['direction']} {cmd['value']} (P{cmd['priority']})")
            print(f"DOOM: {doom_fmt}")
            print()


def main():
    """Run FTP action reader"""
    import argparse
    
    parser = argparse.ArgumentParser(description='FTP Action Reader')
    parser.add_argument('--watch', default='mvs_datasets', help='Directory to watch')
    parser.add_argument('--test', action='store_true', help='Test parser')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    
    args = parser.parse_args()
    
    if args.test:
        test_parser()
        return
        
    reader = FTPActionReader(args.watch)
    reader.start()
    
    print(f"""
╔══════════════════════════════════════════════════════╗
║             FTP Action Reader Active                 ║
╚══════════════════════════════════════════════════════╝

Monitoring: {args.watch}
Files: {', '.join(reader.command_files)}

Commands will be displayed as they arrive...
Press Ctrl+C to stop
""")
    
    try:
        while True:
            commands = reader.get_commands(timeout=1.0)
            for cmd in commands:
                print(f"\n[{cmd['source']}] {cmd['command']}")
                if 'cobol' in cmd:
                    print(f"  Priority: {cmd['cobol']['priority']}")
                    print(f"  Reason: {cmd['cobol']['reason']}")
                    
    except KeyboardInterrupt:
        print("\nStopping...")
        reader.stop()


if __name__ == "__main__":
    main()