#!/usr/bin/env python3
"""
COBOL Mapper - Maps SQLite game state to COBOL structures
Reads from SQLite and writes proper COBOL datasets
"""

import sqlite3
import struct
import os
import logging
from typing import List, Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class COBOLMapper:
    """Maps game state to COBOL data structures"""
    
    def __init__(self, db_path="doom_state.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.datasets_dir = "cobol_datasets"
        os.makedirs(self.datasets_dir, exist_ok=True)
        
    def map_state_to_cobol(self, state_id: int) -> Dict[str, str]:
        """Map a game state to COBOL records"""
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
            return {}
            
        (tick, level, health, armor, x, y, z, angle,
         bullets, shells, cells, rockets, weapon, enemy_count, timestamp) = row
        
        records = {}
        
        # STATE-HEADER record (80 bytes)
        state_header = self._format_state_header(tick, level, timestamp)
        records['STATE'] = state_header
        
        # PLAYER-RECORD (80 bytes)
        player_record = self._format_player_record(x, y, z, angle, health, armor)
        records['PLAYER'] = player_record
        
        # AMMUNITION-RECORD (80 bytes)
        ammo_record = self._format_ammo_record(bullets, shells, cells, rockets, weapon)
        records['AMMO'] = ammo_record
        
        # ENTITY records
        cursor.execute('''
            SELECT enemy_index, type, health, x, y, distance
            FROM enemies WHERE state_id = ?
            ORDER BY enemy_index
        ''', (state_id,))
        
        enemies = cursor.fetchall()
        entity_records = []
        
        for idx, (_, etype, ehealth, ex, ey, distance) in enumerate(enemies[:16]):
            entity_rec = self._format_entity_record(idx, etype, ehealth, ex, ey, distance)
            entity_records.append(entity_rec)
            
        records['ENTITIES'] = entity_records
        
        return records
        
    def _format_state_header(self, tick: int, level: int, timestamp: float) -> str:
        """Format STATE-HEADER record"""
        # Convert timestamp to YYYYMMDD
        dt = datetime.fromtimestamp(timestamp)
        date_str = dt.strftime('%Y%m%d')
        
        record = (
            f"{'STATE   ':<8}"       # STATE-RECORD-TYPE
            f"{tick:08d}"            # STATE-TICK
            f"{level:02d}"           # STATE-LEVEL
            f"{date_str:>8}"         # STATE-TIMESTAMP
            f"{' ' * 52}"            # FILLER
        )
        
        assert len(record) == 80, f"STATE record wrong length: {len(record)}"
        return record
        
    def _format_player_record(self, x: int, y: int, z: int, angle: int, health: int, armor: int) -> str:
        """Format PLAYER-RECORD"""
        # Convert fixed point to map units
        map_x = x >> 16
        map_y = y >> 16
        map_z = z >> 16
        
        # Convert angle to degrees
        degrees = (angle * 360) // 0xFFFFFFFF if angle >= 0 else 0
        
        # Determine status
        status = 'D' if health <= 0 else 'A'
        
        record = (
            f"{'PLAYER  ':<8}"       # PLAYER-RECORD-TYPE
            f"{map_x:+08d}"          # PLAYER-X
            f"{map_y:+08d}"          # PLAYER-Y
            f"{map_z:+08d}"          # PLAYER-Z
            f"{degrees:+04d}"        # PLAYER-ANGLE
            f"{health:03d}"          # PLAYER-HEALTH
            f"{armor:03d}"           # PLAYER-ARMOR
            f"{status}"              # PLAYER-STATUS
            f"{' ' * 8}"             # PLAYER-FLAGS
            f"{' ' * 28}"            # FILLER
        )
        
        assert len(record) == 80, f"PLAYER record wrong length: {len(record)}"
        return record
        
    def _format_ammo_record(self, bullets: int, shells: int, cells: int, rockets: int, weapon: int) -> str:
        """Format AMMUNITION-RECORD"""
        record = (
            f"{'AMMO    ':<8}"      # AMMO-RECORD-TYPE
            f"{bullets:04d}"         # AMMO-BULLETS
            f"{shells:04d}"          # AMMO-SHELLS
            f"{cells:04d}"           # AMMO-CELLS
            f"{rockets:04d}"         # AMMO-ROCKETS
            f"{weapon:01d}"          # CURRENT-WEAPON
            f"{' ' * 55}"            # FILLER
        )
        
        assert len(record) == 80, f"AMMO record wrong length: {len(record)}"
        return record
        
    def _format_entity_record(self, idx: int, etype: int, health: int, x: int, y: int, distance: int) -> str:
        """Format ENTITY record"""
        # Convert positions
        map_x = x >> 16
        map_y = y >> 16
        map_dist = distance >> 16
        
        # Calculate angle to entity (simplified)
        angle_to = 0  # Would need player position to calculate properly
        
        record = (
            f"{'ENEMY   ':<8}"       # ENTITY-RECORD-TYPE
            f"{etype:02d}"           # ENTITY-TYPE
            f"{health:03d}"          # ENTITY-HEALTH
            f"{map_x:+08d}"          # ENTITY-X
            f"{map_y:+08d}"          # ENTITY-Y
            f"{map_dist:05d}"        # ENTITY-DISTANCE
            f"{angle_to:+03d}"       # ENTITY-ANGLE-TO
            f"{' ' * 8}"             # ENTITY-FLAGS
            f"{' ' * 30}"            # FILLER
        )
        
        assert len(record) == 80, f"ENTITY record wrong length: {len(record)}"
        return record
        
    def write_datasets(self, state_id: int):
        """Write COBOL datasets for a game state"""
        records = self.map_state_to_cobol(state_id)
        
        if not records:
            logger.error(f"No state found for ID {state_id}")
            return
            
        # Write STATE dataset
        with open(f"{self.datasets_dir}/DOOM.STATE", 'w') as f:
            f.write(records['STATE'] + '\n')
            
        # Write PLAYER dataset
        with open(f"{self.datasets_dir}/DOOM.PLAYER", 'w') as f:
            f.write(records['PLAYER'] + '\n')
            
        # Write AMMO dataset
        with open(f"{self.datasets_dir}/DOOM.AMMO", 'w') as f:
            f.write(records['AMMO'] + '\n')
            
        # Write ENTITIES dataset
        with open(f"{self.datasets_dir}/DOOM.ENTITIES", 'w') as f:
            for entity in records['ENTITIES']:
                f.write(entity + '\n')
                
        logger.info(f"Wrote COBOL datasets for state {state_id}")
        
    def write_gamestat_dataset(self, state_id: int):
        """Write combined GAMESTAT dataset (all records)"""
        records = self.map_state_to_cobol(state_id)
        
        if not records:
            return
            
        with open(f"{self.datasets_dir}/DOOM.GAMESTAT", 'w') as f:
            f.write(records['STATE'] + '\n')
            f.write(records['PLAYER'] + '\n')
            f.write(records['AMMO'] + '\n')
            for entity in records['ENTITIES']:
                f.write(entity + '\n')
                
        logger.info(f"Wrote DOOM.GAMESTAT for state {state_id}")
        
    def process_latest_states(self, count=10):
        """Process the latest N states"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id FROM game_state
            ORDER BY id DESC
            LIMIT ?
        ''', (count,))
        
        for (state_id,) in cursor.fetchall():
            self.write_gamestat_dataset(state_id)
            
    def verify_mapping(self):
        """Verify COBOL mapping is correct"""
        logger.info("Verifying COBOL mapping...")
        
        # Check record lengths
        test_state_id = self.conn.execute("SELECT MAX(id) FROM game_state").fetchone()[0]
        if not test_state_id:
            logger.warning("No states to verify")
            return
            
        records = self.map_state_to_cobol(test_state_id)
        
        # Verify all records are 80 bytes
        for rec_type, rec_data in records.items():
            if rec_type == 'ENTITIES':
                for entity in rec_data:
                    assert len(entity) == 80, f"Entity record wrong length: {len(entity)}"
            else:
                assert len(rec_data) == 80, f"{rec_type} record wrong length: {len(rec_data)}"
                
        logger.info("✓ All COBOL records are properly formatted (80 bytes)")
        
        # Show sample
        logger.info("\nSample COBOL records:")
        logger.info("STATE:  " + records['STATE'][:40] + "...")
        logger.info("PLAYER: " + records['PLAYER'][:40] + "...")
        logger.info("AMMO:   " + records['AMMO'][:40] + "...")


def main():
    """Test the COBOL mapper"""
    import argparse
    
    parser = argparse.ArgumentParser(description='COBOL State Mapper')
    parser.add_argument('--db', default='doom_state.db', help='SQLite database path')
    parser.add_argument('--verify', action='store_true', help='Verify mapping')
    parser.add_argument('--latest', type=int, help='Process latest N states')
    parser.add_argument('--state', type=int, help='Process specific state ID')
    
    args = parser.parse_args()
    
    mapper = COBOLMapper(args.db)
    
    if args.verify:
        mapper.verify_mapping()
        
    if args.latest:
        mapper.process_latest_states(args.latest)
        
    if args.state:
        mapper.write_gamestat_dataset(args.state)
        logger.info(f"\nDatasets written to {mapper.datasets_dir}/")
        
    # Show what's available
    cursor = mapper.conn.cursor()
    count = cursor.execute("SELECT COUNT(*) FROM game_state").fetchone()[0]
    logger.info(f"\nTotal states in database: {count}")
    

if __name__ == "__main__":
    main()