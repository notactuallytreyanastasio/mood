#!/usr/bin/env python3
"""
Test script for FTP Command Monitor
Creates test DOOM.COMMANDS file with sample commands
"""

import os
import time
from pathlib import Path

def create_test_commands():
    """Create test DOOM.COMMANDS file with sample COBOL records"""
    
    # Create directory
    commands_dir = Path("cobol_datasets")
    commands_dir.mkdir(exist_ok=True)
    
    commands_file = commands_dir / "DOOM.COMMANDS"
    
    # Sample commands in DOOM-COMMAND-RECORD format (80 bytes each)
    # Format: RECORD_TYPE(8) ACTION(8) DIRECTION(8) VALUE(4) PRIORITY(1) REASON(20) FILLER(31)
    commands = [
        # Move forward for 2 seconds (value=20 -> 20/10 = 2.0 seconds)
        "COMMAND MOVE    FORWARD 00201ENEMY APPROACHING       " + " " * 31,
        
        # Turn right 45 degrees
        "COMMAND TURN    RIGHT   00459SCAN FOR THREATS        " + " " * 31,
        
        # Shoot 3 times
        "COMMAND SHOOT           00037DEMON IN SIGHT          " + " " * 31,
        
        # Move backward for 1 second
        "COMMAND MOVE    BACK    00109TACTICAL RETREAT        " + " " * 31,
        
        # Wait for 1 second
        "COMMAND WAIT            00105REGROUP                 " + " " * 31,
    ]
    
    print(f"Writing {len(commands)} test commands to {commands_file}")
    
    # Write as binary file with fixed 80-byte records
    with open(commands_file, 'wb') as f:
        for cmd in commands:
            # Ensure exactly 80 bytes
            record = cmd[:80].ljust(80)
            f.write(record.encode('ascii'))
            print(f"  Written: {record[:49]}...")  # Show first 49 chars
            
    print(f"\nFile created: {commands_file}")
    print(f"File size: {os.path.getsize(commands_file)} bytes")
    print(f"Expected: {len(commands) * 80} bytes")
    

def test_ebcdic_commands():
    """Create test file with EBCDIC-encoded commands"""
    
    commands_dir = Path("cobol_datasets")
    commands_dir.mkdir(exist_ok=True)
    
    commands_file = commands_dir / "DOOM.COMMANDS.EBCDIC"
    
    # Same commands but EBCDIC encoded
    commands = [
        "COMMAND MOVE    FORWARD 00201ENEMY APPROACHING       " + " " * 31,
        "COMMAND TURN    RIGHT   00459SCAN FOR THREATS        " + " " * 31,
    ]
    
    print(f"\nWriting EBCDIC test commands to {commands_file}")
    
    with open(commands_file, 'wb') as f:
        for cmd in commands:
            record = cmd[:80].ljust(80)
            # Convert to EBCDIC
            ebcdic_record = record.encode('cp037')
            f.write(ebcdic_record)
            print(f"  Written (EBCDIC): {record[:49]}...")
            

def main():
    """Run tests"""
    print("FTP Command Monitor Test Script")
    print("=" * 50)
    
    # Create ASCII test file
    create_test_commands()
    
    # Create EBCDIC test file
    test_ebcdic_commands()
    
    print("\nTest files created successfully!")
    print("\nTo test the monitor, run:")
    print("  python3 build_system/ftp_command_monitor.py")
    print("\nThen check status at:")
    print("  curl http://localhost:8888/status")
    print("  curl http://localhost:8888/commands")
    

if __name__ == "__main__":
    main()