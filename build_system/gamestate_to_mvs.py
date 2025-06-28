#!/usr/bin/env python3
"""
Game State to MVS Dataset Converter
Converts SQLite game state to MVS dataset format for FTP to z/OS
"""

import sqlite3
import struct
import os
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GameStateToMVS:
    """Convert game state to MVS dataset format"""
    
    def __init__(self, db_path="doom_state.db", output_dir="mvs_datasets"):
        self.db_path = db_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        
    def get_latest_state(self):
        """Get the most recent game state"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, tick, level, health, armor, x, y, z, angle,
                   ammo_bullets, ammo_shells, ammo_cells, ammo_rockets,
                   weapon, enemy_count, timestamp
            FROM game_state
            ORDER BY id DESC
            LIMIT 1
        ''')
        return cursor.fetchone()
        
    def format_as_mvs_dataset(self, state_id):
        """Format game state as MVS dataset (RECFM=FB LRECL=80)"""
        cursor = self.conn.cursor()
        
        # Get main state
        cursor.execute('''
            SELECT tick, level, health, armor, x, y, z, angle,
                   ammo_bullets, ammo_shells, ammo_cells, ammo_rockets,
                   weapon, enemy_count, timestamp
            FROM game_state WHERE id = ?
        ''', (state_id,))
        
        row = cursor.fetchone()
        if not row:
            return []
            
        (tick, level, health, armor, x, y, z, angle,
         bullets, shells, cells, rockets, weapon, enemy_count, timestamp) = row
        
        records = []
        
        # Record 1: STATE header (80 bytes)
        dt = datetime.fromtimestamp(timestamp)
        state_rec = (
            f"{'STATE   ':<8}"
            f"{tick:08d}"
            f"{level:02d}"
            f"{dt.strftime('%Y%m%d'):>8}"
            f"{' ' * 52}"
        )
        records.append(state_rec)
        
        # Record 2: PLAYER data (80 bytes)
        map_x = x >> 16  # Convert fixed point
        map_y = y >> 16
        map_z = z >> 16
        degrees = (angle * 360) // 0xFFFFFFFF if angle >= 0 else 0
        status = 'D' if health <= 0 else 'A'
        
        player_rec = (
            f"{'PLAYER  ':<8}"
            f"{map_x:+08d}"
            f"{map_y:+08d}"
            f"{map_z:+08d}"
            f"{degrees:+04d}"
            f"{health:03d}"
            f"{armor:03d}"
            f"{status}"
            f"{' ' * 8}"
            f"{' ' * 28}"
        )
        records.append(player_rec)
        
        # Record 3: AMMO data (80 bytes)
        ammo_rec = (
            f"{'AMMO    ':<8}"
            f"{bullets:04d}"
            f"{shells:04d}"
            f"{cells:04d}"
            f"{rockets:04d}"
            f"{weapon:01d}"
            f"{' ' * 55}"
        )
        records.append(ammo_rec)
        
        # Records 4+: ENEMY data (80 bytes each)
        cursor.execute('''
            SELECT enemy_index, type, health, x, y, distance
            FROM enemies WHERE state_id = ?
            ORDER BY enemy_index
            LIMIT 16
        ''', (state_id,))
        
        for idx, (_, etype, ehealth, ex, ey, distance) in enumerate(cursor.fetchall()):
            map_ex = ex >> 16
            map_ey = ey >> 16
            map_dist = distance >> 16
            
            enemy_rec = (
                f"{'ENEMY   ':<8}"
                f"{etype:02d}"
                f"{ehealth:03d}"
                f"{map_ex:+08d}"
                f"{map_ey:+08d}"
                f"{map_dist:05d}"
                f"{0:+03d}"  # angle_to
                f"{' ' * 8}"
                f"{' ' * 30}"
            )
            records.append(enemy_rec)
            
        return records
        
    def write_mvs_dataset(self, records, filename):
        """Write records as MVS dataset file"""
        filepath = self.output_dir / filename
        
        # Write as EBCDIC encoded fixed-block dataset
        with open(filepath, 'wb') as f:
            for record in records:
                # Ensure exactly 80 bytes
                if len(record) != 80:
                    logger.warning(f"Record wrong length: {len(record)}")
                    record = record[:80].ljust(80)
                    
                # Convert to EBCDIC
                ebcdic_record = record.encode('cp037')
                f.write(ebcdic_record)
                
        # Also write ASCII version for debugging
        ascii_path = self.output_dir / f"{filename}.ASCII"
        with open(ascii_path, 'w') as f:
            for record in records:
                f.write(record + '\n')
                
        logger.info(f"Wrote MVS dataset: {filepath}")
        logger.info(f"  Records: {len(records)}")
        logger.info(f"  LRECL: 80")
        logger.info(f"  ASCII copy: {ascii_path}")
        
    def create_current_gamestat(self):
        """Create GAMESTAT.CURRENT dataset from latest state"""
        state = self.get_latest_state()
        if not state:
            logger.error("No game state found in database")
            return False
            
        state_id = state[0]
        logger.info(f"Converting state {state_id} to MVS dataset")
        
        records = self.format_as_mvs_dataset(state_id)
        self.write_mvs_dataset(records, "DOOM.GAMESTAT")
        
        # Create symlink for FTP
        current_link = self.output_dir / "GAMESTAT.CURRENT"
        if current_link.exists():
            current_link.unlink()
        current_link.symlink_to("DOOM.GAMESTAT")
        
        return True
        
    def monitor_and_convert(self, interval=1):
        """Monitor database and convert new states"""
        logger.info(f"Monitoring game states every {interval} seconds")
        
        last_state_id = None
        
        try:
            while True:
                state = self.get_latest_state()
                if state:
                    state_id = state[0]
                    if state_id != last_state_id:
                        logger.info(f"New state detected: {state_id}")
                        self.create_current_gamestat()
                        last_state_id = state_id
                        
                import time
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped")
            
    def test_conversion(self):
        """Test with sample data"""
        # Create test records
        test_records = [
            "STATE   00001234012025010100000000000000000000000000000000000000000000000000000",
            "PLAYER  +0001024+0001024+0000000+090075050A        0000000000000000000000000000",
            "AMMO    0050002001000040200000000000000000000000000000000000000000000000000000",
            "ENEMY   09100+0001200+0001100002560000        000000000000000000000000000000000",
            "ENEMY   02075+0000800+0000900001280000        000000000000000000000000000000000",
        ]
        
        self.write_mvs_dataset(test_records, "TEST.GAMESTAT")
        
        # Verify
        test_file = self.output_dir / "TEST.GAMESTAT"
        size = test_file.stat().st_size
        expected = len(test_records) * 80
        
        if size == expected:
            logger.info(f"✓ Test passed: {size} bytes written")
        else:
            logger.error(f"✗ Test failed: expected {expected} bytes, got {size}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Game State to MVS Converter')
    parser.add_argument('--db', default='doom_state.db', help='SQLite database')
    parser.add_argument('--output', default='mvs_datasets', help='Output directory')
    parser.add_argument('--monitor', action='store_true', help='Monitor continuously')
    parser.add_argument('--test', action='store_true', help='Run test conversion')
    parser.add_argument('--once', action='store_true', help='Convert once and exit')
    
    args = parser.parse_args()
    
    converter = GameStateToMVS(args.db, args.output)
    
    if args.test:
        converter.test_conversion()
    elif args.monitor:
        converter.monitor_and_convert()
    elif args.once:
        if converter.create_current_gamestat():
            print(f"Dataset created in {args.output}/")
    else:
        # Default: convert once
        if converter.create_current_gamestat():
            print(f"Dataset created in {args.output}/")
            print("\nTo monitor continuously, use --monitor")


if __name__ == "__main__":
    main()