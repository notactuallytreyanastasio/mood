#!/usr/bin/env python3
"""
Complete State Monitor - UDP, File, and SQLite
Monitors DOOM state from multiple sources
"""

import socket
import time
import os
import threading
import logging
from doom_state_sqlite import DoomStateSQLite

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CompleteStateMonitor:
    """Monitors DOOM state from UDP and writes to multiple outputs"""
    
    def __init__(self):
        self.running = False
        self.sqlite_capture = DoomStateSQLite()
        self.state_file = "/tmp/doom_state.dat"
        self.last_state = None
        
    def start(self):
        """Start all monitoring"""
        self.running = True
        
        # Start SQLite capture (handles UDP)
        self.sqlite_capture.start_capture()
        
        # Start file writer
        file_thread = threading.Thread(target=self._file_writer_loop)
        file_thread.start()
        
        # Start file monitor (for testing without UDP)
        monitor_thread = threading.Thread(target=self._file_monitor_loop)
        monitor_thread.start()
        
        logger.info("Complete state monitor started")
        logger.info(f"- UDP capture on port {self.sqlite_capture.port}")
        logger.info(f"- File output to {self.state_file}")
        logger.info(f"- SQLite database: {self.sqlite_capture.db_path}")
        
    def _file_writer_loop(self):
        """Write latest state to file in COBOL format"""
        while self.running:
            try:
                # Get latest state from SQLite
                states = self.sqlite_capture.query_recent_states(1)
                if states:
                    # Get COBOL format
                    cursor = self.sqlite_capture.conn.cursor()
                    cursor.execute('''
                        SELECT record_data 
                        FROM cobol_state 
                        WHERE state_id = (SELECT MAX(id) FROM game_state)
                        ORDER BY id
                    ''')
                    
                    records = cursor.fetchall()
                    if records:
                        with open(self.state_file, 'w') as f:
                            for record in records:
                                f.write(record[0] + '\n')
                                
                time.sleep(0.1)  # 10Hz
                
            except Exception as e:
                logger.error(f"File writer error: {e}")
                time.sleep(1)
                
    def _file_monitor_loop(self):
        """Monitor file changes (backup method)"""
        last_mtime = 0
        
        while self.running:
            try:
                if os.path.exists(self.state_file):
                    mtime = os.path.getmtime(self.state_file)
                    if mtime > last_mtime:
                        last_mtime = mtime
                        logger.info(f"State file updated: {self.state_file}")
                        
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"File monitor error: {e}")
                
    def stop(self):
        """Stop all monitoring"""
        self.running = False
        self.sqlite_capture.stop_capture()
        

def main():
    """Run the complete monitor"""
    monitor = CompleteStateMonitor()
    monitor.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop()
        

if __name__ == "__main__":
    main()