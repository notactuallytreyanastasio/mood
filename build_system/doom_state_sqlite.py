#!/usr/bin/env python3
"""
DOOM State SQLite Dumper
Captures game state from UDP and stores in SQLite for analysis
"""

import socket
import struct
import sqlite3
import time
import json
import threading
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


class DoomStateSQLite:
    """Captures DOOM state and stores in SQLite database"""
    
    def __init__(self, db_path="doom_state.db", port=31337):
        self.db_path = db_path
        self.port = port
        self.socket = None
        self.conn = None
        self.running = False
        self.stats = {
            'packets_received': 0,
            'last_tick': 0,
            'start_time': time.time()
        }
        
    def init_database(self):
        """Initialize SQLite database schema"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        
        # Main game state table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                tick INTEGER,
                level INTEGER,
                health INTEGER,
                armor INTEGER,
                x INTEGER,
                y INTEGER,
                z INTEGER,
                angle INTEGER,
                momx INTEGER,
                momy INTEGER,
                weapon INTEGER,
                ammo_bullets INTEGER,
                ammo_shells INTEGER,
                ammo_cells INTEGER,
                ammo_rockets INTEGER,
                kills INTEGER,
                items INTEGER,
                secrets INTEGER,
                enemy_count INTEGER,
                raw_data BLOB
            )
        ''')
        
        # Enemy tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enemies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                state_id INTEGER,
                enemy_index INTEGER,
                type INTEGER,
                health INTEGER,
                x INTEGER,
                y INTEGER,
                distance INTEGER,
                FOREIGN KEY (state_id) REFERENCES game_state(id)
            )
        ''')
        
        # Session info table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time REAL,
                end_time REAL,
                total_packets INTEGER,
                notes TEXT
            )
        ''')
        
        # COBOL format table (for easy mapping)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cobol_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                state_id INTEGER,
                record_type TEXT,
                record_data TEXT,
                FOREIGN KEY (state_id) REFERENCES game_state(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tick ON game_state(tick)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON game_state(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_health ON game_state(health)')
        
        self.conn.commit()
        
        # Start new session
        cursor.execute(
            'INSERT INTO sessions (start_time, total_packets) VALUES (?, 0)',
            (time.time(),)
        )
        self.session_id = cursor.lastrowid
        self.conn.commit()
        
        logger.info(f"Database initialized: {self.db_path}")
        logger.info(f"Session ID: {self.session_id}")
        
    def start_capture(self):
        """Start capturing state from UDP"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('0.0.0.0', self.port))
        self.socket.settimeout(0.1)
        
        self.running = True
        self.init_database()
        
        logger.info(f"Listening for DOOM state on UDP port {self.port}")
        
        # Start capture thread
        capture_thread = threading.Thread(target=self._capture_loop)
        capture_thread.start()
        
        # Start stats thread
        stats_thread = threading.Thread(target=self._stats_loop)
        stats_thread.start()
        
    def _capture_loop(self):
        """Main capture loop"""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(4096)
                self._process_packet(data)
                self.stats['packets_received'] += 1
                
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Capture error: {e}")
                
    def _process_packet(self, data: bytes):
        """Process received state packet"""
        if len(data) < 88:  # Minimum packet size
            return
            
        try:
            # Parse binary state structure
            state = self._parse_state(data)
            
            # Store in database
            self._store_state(state, data)
            
            # Update stats
            self.stats['last_tick'] = state['tick']
            
        except Exception as e:
            logger.error(f"Failed to process packet: {e}")
            
    def _parse_state(self, data: bytes) -> Dict[str, Any]:
        """Parse binary state packet"""
        # Header (12 bytes)
        magic, version, tick = struct.unpack('<III', data[0:12])
        
        if magic != 0x4D4F4F44:  # 'DOOM'
            raise ValueError("Invalid magic number")
            
        # Player state (52 bytes)
        (health, armor, 
         ammo0, ammo1, ammo2, ammo3,
         weapon, x, y, z, angle, momx, momy,
         level, kills, items, secrets,
         enemy_count) = struct.unpack('<18i', data[12:84])
        
        state = {
            'tick': tick,
            'level': level,
            'health': health,
            'armor': armor,
            'x': x,
            'y': y,
            'z': z,
            'angle': angle,
            'momx': momx,
            'momy': momy,
            'weapon': weapon,
            'ammo': [ammo0, ammo1, ammo2, ammo3],
            'kills': kills,
            'items': items,
            'secrets': secrets,
            'enemy_count': enemy_count,
            'enemies': []
        }
        
        # Parse enemies
        offset = 88
        for i in range(min(enemy_count, 16)):
            if offset + 20 <= len(data):
                enemy = struct.unpack('<5i', data[offset:offset+20])
                state['enemies'].append({
                    'type': enemy[0],
                    'health': enemy[1],
                    'x': enemy[2],
                    'y': enemy[3],
                    'distance': enemy[4]
                })
                offset += 20
                
        return state
        
    def _store_state(self, state: Dict[str, Any], raw_data: bytes):
        """Store state in database"""
        cursor = self.conn.cursor()
        
        # Insert main state
        cursor.execute('''
            INSERT INTO game_state (
                timestamp, tick, level, health, armor,
                x, y, z, angle, momx, momy, weapon,
                ammo_bullets, ammo_shells, ammo_cells, ammo_rockets,
                kills, items, secrets, enemy_count, raw_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            time.time(), state['tick'], state['level'],
            state['health'], state['armor'],
            state['x'], state['y'], state['z'], state['angle'],
            state['momx'], state['momy'], state['weapon'],
            state['ammo'][0], state['ammo'][1], state['ammo'][2], state['ammo'][3],
            state['kills'], state['items'], state['secrets'],
            state['enemy_count'], raw_data
        ))
        
        state_id = cursor.lastrowid
        
        # Insert enemies
        for i, enemy in enumerate(state['enemies']):
            cursor.execute('''
                INSERT INTO enemies (
                    state_id, enemy_index, type, health, x, y, distance
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                state_id, i, enemy['type'], enemy['health'],
                enemy['x'], enemy['y'], enemy['distance']
            ))
            
        # Generate COBOL format records
        self._store_cobol_format(cursor, state_id, state)
        
        self.conn.commit()
        
    def _store_cobol_format(self, cursor, state_id: int, state: Dict[str, Any]):
        """Store COBOL-formatted records"""
        # STATE record
        cursor.execute(
            'INSERT INTO cobol_state (state_id, record_type, record_data) VALUES (?, ?, ?)',
            (state_id, 'STATE', f"STATE {state['tick']:08d} {state['level']:02d}")
        )
        
        # PLAYER record
        x = state['x'] >> 16  # Convert fixed point
        y = state['y'] >> 16
        z = state['z'] >> 16
        angle = (state['angle'] * 360) // 0xFFFFFFFF  # BAM to degrees
        
        player_rec = f"PLAYER{x:+08d}{y:+08d}{z:+08d}{angle:+04d}{state['health']:03d}{state['armor']:03d}"
        cursor.execute(
            'INSERT INTO cobol_state (state_id, record_type, record_data) VALUES (?, ?, ?)',
            (state_id, 'PLAYER', player_rec)
        )
        
        # AMMO record
        ammo_rec = f"AMMO  {state['ammo'][0]:04d}{state['ammo'][1]:04d}{state['ammo'][2]:04d}{state['ammo'][3]:04d} {state['weapon']}"
        cursor.execute(
            'INSERT INTO cobol_state (state_id, record_type, record_data) VALUES (?, ?, ?)',
            (state_id, 'AMMO', ammo_rec)
        )
        
        # ENEMY records
        for enemy in state['enemies']:
            enemy_x = enemy['x'] >> 16
            enemy_y = enemy['y'] >> 16
            enemy_dist = enemy['distance'] >> 16
            
            enemy_rec = f"ENEMY {enemy['type']:02d} {enemy['health']:03d} {enemy_x:+08d} {enemy_y:+08d} {enemy_dist:05d}"
            cursor.execute(
                'INSERT INTO cobol_state (state_id, record_type, record_data) VALUES (?, ?, ?)',
                (state_id, 'ENEMY', enemy_rec)
            )
            
    def _stats_loop(self):
        """Report statistics periodically"""
        while self.running:
            time.sleep(5)
            
            runtime = time.time() - self.stats['start_time']
            pps = self.stats['packets_received'] / runtime if runtime > 0 else 0
            
            logger.info(
                f"Stats - Packets: {self.stats['packets_received']}, "
                f"Last tick: {self.stats['last_tick']}, "
                f"Rate: {pps:.1f}/sec"
            )
            
            # Update session
            cursor = self.conn.cursor()
            cursor.execute(
                'UPDATE sessions SET total_packets = ? WHERE id = ?',
                (self.stats['packets_received'], self.session_id)
            )
            self.conn.commit()
            
    def query_recent_states(self, limit=10):
        """Query recent game states"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT tick, health, armor, x, y, enemy_count
            FROM game_state
            ORDER BY id DESC
            LIMIT ?
        ''', (limit,))
        
        return cursor.fetchall()
        
    def export_cobol_format(self, output_file='doom_state_cobol.txt'):
        """Export recent states in COBOL format"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT record_data
            FROM cobol_state
            WHERE state_id IN (
                SELECT id FROM game_state ORDER BY id DESC LIMIT 10
            )
            ORDER BY state_id DESC, id
        ''')
        
        with open(output_file, 'w') as f:
            for row in cursor.fetchall():
                f.write(row[0] + '\n')
                
        logger.info(f"Exported COBOL format to {output_file}")
        
    def stop_capture(self):
        """Stop capturing"""
        self.running = False
        
        if self.conn:
            cursor = self.conn.cursor()
            cursor.execute(
                'UPDATE sessions SET end_time = ? WHERE id = ?',
                (time.time(), self.session_id)
            )
            self.conn.commit()
            self.conn.close()
            
        if self.socket:
            self.socket.close()
            

def main():
    """Run the state capture"""
    print("DOOM State SQLite Capture")
    print("=" * 50)
    print()
    print("This captures DOOM state from UDP port 31337")
    print("and stores it in SQLite for analysis")
    print()
    
    capture = DoomStateSQLite()
    capture.start_capture()
    
    print("Capture running. Press Ctrl+C to stop")
    print()
    print("To query the database:")
    print("  sqlite3 doom_state.db")
    print("  SELECT * FROM game_state ORDER BY id DESC LIMIT 10;")
    print()
    
    try:
        while True:
            time.sleep(10)
            
            # Show recent states
            print("\nRecent states:")
            states = capture.query_recent_states(5)
            print("Tick    Health  Armor   X       Y       Enemies")
            print("-" * 50)
            for state in states:
                tick, health, armor, x, y, enemies = state
                print(f"{tick:<8} {health:<7} {armor:<7} {x>>16:<8} {y>>16:<8} {enemies}")
                
    except KeyboardInterrupt:
        print("\nStopping capture...")
        capture.stop_capture()
        
        # Export COBOL format
        capture.export_cobol_format()
        
        print(f"\nDatabase saved to: doom_state.db")
        print(f"Total packets: {capture.stats['packets_received']}")
        

if __name__ == "__main__":
    main()