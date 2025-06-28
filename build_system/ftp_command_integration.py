#!/usr/bin/env python3
"""
Integration script showing how FTP Command Monitor works with the FTP Gateway
"""

import socket
import time
import threading
from pathlib import Path

def send_to_cobol_interface(command: str, host: str = 'localhost', port: int = 9999):
    """Send command to COBOL interface"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.send(f"{command}\n".encode())
        response = sock.recv(1024)
        sock.close()
        return response.decode().strip()
    except Exception as e:
        return f"Error: {e}"


def demo_integration():
    """Demonstrate the full integration flow"""
    
    print("DOOM-COBOL FTP Command Integration Demo")
    print("=" * 50)
    print()
    print("This demonstrates how commands flow through the system:")
    print()
    print("1. COBOL program (DOOMAI2.COB) writes commands to DOOM.COMMANDS")
    print("2. ftp_command_monitor.py watches this file for updates")
    print("3. Commands are parsed and made available via:")
    print("   - FTP gateway (as DOOM.COMMANDS.OUT dataset)")
    print("   - HTTP status API (for monitoring)")
    print("4. FTP gateway can download commands and send to DOOM")
    print()
    
    # Show example command processing
    print("Example COBOL Command Record (80 bytes):")
    print("┌─────────┬─────────┬─────────┬──────┬────┬────────────────────┬─────────────────────────────────┐")
    print("│ REC_TYPE│ ACTION  │DIRECTION│VALUE │PRI │ REASON             │ FILLER (31 bytes)               │")
    print("├─────────┼─────────┼─────────┼──────┼────┼────────────────────┼─────────────────────────────────┤")
    print("│COMMAND  │MOVE     │FORWARD  │0020  │1   │ENEMY APPROACHING   │                                 │")
    print("└─────────┴─────────┴─────────┴──────┴────┴────────────────────┴─────────────────────────────────┘")
    print()
    
    print("This gets parsed into:")
    print("- Action: MOVE")
    print("- Direction: FORWARD")
    print("- Value: 20 (2.0 seconds)")
    print("- Priority: 1 (low)")
    print("- Reason: ENEMY APPROACHING")
    print()
    
    print("Which becomes COBOL interface command: 'MOVE FORWARD 2.0'")
    print()
    
    # Show integration points
    print("Integration with existing components:")
    print()
    print("1. With ftp_gateway.py:")
    print("   - ftp_gateway.py downloads from DOOM.COMMANDS.OUT")
    print("   - Parses commands and sends to COBOL interface port 9999")
    print()
    print("2. With MVS/Hercules:")
    print("   - Real MVS would write to DOOM.COMMANDS dataset")
    print("   - FTP server makes dataset available for download")
    print("   - ftp_command_monitor.py provides gateway functionality")
    print()
    print("3. With COBOL Interface:")
    print("   - Commands converted to expected format")
    print("   - Sent via TCP to port 9999")
    print("   - COBOL interface translates to DOOM actions")
    print()


def show_architecture():
    """Show the system architecture"""
    
    print("\nSystem Architecture:")
    print("=" * 50)
    print()
    print("    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐")
    print("    │  DOOMAI2    │     │   Hercules  │     │  Mock MVS   │")
    print("    │   (COBOL)   │     │  MVS/3.8j   │     │  (Python)   │")
    print("    └──────┬──────┘     └──────┬──────┘     └──────┬──────┘")
    print("           │                   │                    │")
    print("           │ Writes            │ Writes            │ Writes")
    print("           ▼                   ▼                    ▼")
    print("    ┌─────────────────────────────────────────────────────┐")
    print("    │              DOOM.COMMANDS Dataset                  │")
    print("    │            (80-byte COBOL records)                  │")
    print("    └─────────────────────┬───────────────────────────────┘")
    print("                          │")
    print("                          │ Monitors")
    print("                          ▼")
    print("    ┌─────────────────────────────────────────────────────┐")
    print("    │           ftp_command_monitor.py                    │")
    print("    │  - Watches file for updates                         │")
    print("    │  - Parses DOOM-COMMAND-RECORD format                │")
    print("    │  - Handles EBCDIC/ASCII conversion                  │")
    print("    └──────┬─────────────────────┬────────────────────────┘")
    print("           │                     │")
    print("           │ FTP Gateway         │ HTTP API")
    print("           ▼                     ▼")
    print("    ┌──────────────┐      ┌──────────────┐")
    print("    │ FTP Server   │      │ Status API   │")
    print("    │ Dataset:     │      │ Port 8888    │")
    print("    │ DOOM.CMDS.OUT│      │ /status      │")
    print("    └──────┬───────┘      │ /commands    │")
    print("           │              └──────────────┘")
    print("           │ Downloads")
    print("           ▼")
    print("    ┌──────────────┐")
    print("    │ ftp_gateway  │")
    print("    │    .py       │")
    print("    └──────┬───────┘")
    print("           │ Sends commands")
    print("           ▼")
    print("    ┌──────────────┐      ┌──────────────┐")
    print("    │ COBOL        │      │    DOOM      │")
    print("    │ Interface    │─────►│   (Game)     │")
    print("    │ Port 9999    │      │              │")
    print("    └──────────────┘      └──────────────┘")
    print()


def main():
    """Run the demo"""
    demo_integration()
    show_architecture()
    
    print("\nUsage Examples:")
    print("=" * 50)
    print()
    print("1. Start the command monitor:")
    print("   python3 build_system/ftp_command_monitor.py")
    print()
    print("2. Create test commands:")
    print("   python3 build_system/test_ftp_command_monitor.py")
    print()
    print("3. Check status via HTTP:")
    print("   curl http://localhost:8888/status")
    print("   curl http://localhost:8888/commands")
    print()
    print("4. Monitor with custom paths:")
    print("   python3 build_system/ftp_command_monitor.py \\")
    print("     --commands-file /path/to/DOOM.COMMANDS \\")
    print("     --ftp-host mvs.example.com \\")
    print("     --status-port 8080")
    print()
    

if __name__ == "__main__":
    main()