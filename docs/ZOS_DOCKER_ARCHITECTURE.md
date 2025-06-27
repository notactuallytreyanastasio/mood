# z/OS Docker Architecture for DOOM-COBOL Integration

## Overview
To run JCL and COBOL programs that control DOOM, we need a z/OS environment. Docker provides a practical way to run mainframe emulation on modern systems.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                      Host System (Linux/macOS)              │
├─────────────────────┬───────────────────┬──────────────────┤
│   DOOM Process      │  Bridge Service   │ Docker Container │
│   (Native)          │  (Python/Go)      │ (z/OS)           │
│                     │                   │                  │
│  ┌─────────────┐   │ ┌──────────────┐ │ ┌──────────────┐ │
│  │             │   │ │State Extract │ │ │   MVS/zOS    │ │
│  │   DOOM.EXE  │◀──┼─┤              │ │ │              │ │
│  │             │   │ │Input Bridge  │ │ │  JCL Jobs    │ │
│  └─────────────┘   │ │              │ │ │  COBOL Progs │ │
│         ▲          │ │FTP Server    │ │ │              │ │
│         │          │ │              │ │ └──────────────┘ │
│         └──────────┼─┤Dataset Sync  │◀┼─────────┘        │
│                    │ └──────────────┘ │                  │
└────────────────────┴───────────────────┴──────────────────┘
```

## z/OS Docker Options

### Option 1: IBM Z Development and Test Environment (ZD&T)
- Official IBM solution
- Full z/OS compatibility
- Requires license
- Best for production-quality testing

### Option 2: Hercules Emulator + MVS 3.8j
- Open source mainframe emulator
- Runs MVS 3.8j (public domain OS)
- Free to use
- Good enough for COBOL/JCL development

### Option 3: KICKS for TSO
- Lightweight CICS emulator
- Runs on Docker easily
- Limited functionality but fast

## Recommended Setup: Hercules + MVS 3.8j

### Docker Compose Configuration
```yaml
version: '3.8'
services:
  mainframe:
    image: rattydave/docker-ubuntu-hercules-mvs:latest
    container_name: doom-mvs
    ports:
      - "3270:3270"  # TN3270 terminal
      - "8038:8038"  # HTTP console
      - "2121:21"    # FTP for file transfer
    volumes:
      - ./mvs-data:/hercules/data
      - ./doom-datasets:/hercules/doom
    environment:
      - HERCULES_RC=/hercules/scripts/doom.rc
    networks:
      - doom-net

  bridge:
    build: ./bridge
    container_name: doom-bridge
    depends_on:
      - mainframe
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
      - ./bridge-data:/data
    environment:
      - DISPLAY=${DISPLAY}
      - MVS_HOST=mainframe
      - MVS_FTP_PORT=21
    network_mode: host
    privileged: true  # For process memory access

networks:
  doom-net:
    driver: bridge
```

## Data Flow Design

### 1. State Extraction Pipeline
```
DOOM Process → Memory Reader → JSON/Binary → FTP → MVS Dataset
                     ↓
              Bridge Service
                     ↓
            DOOM.STATE (FB 80)
            DOOM.ENTITIES (FB 120)
            DOOM.VIEWPORT (FB 133)
```

### 2. Command Execution Pipeline
```
MVS Dataset → FTP → Bridge Service → X11/Win32 Events → DOOM
     ↑                                                      
DOOM.COMMANDS (FB 80)                                      
     ↑
COBOL Program Output
```

## MVS Dataset Configuration

### JCL for Dataset Allocation
```jcl
//DOOMDEFS JOB (ACCT),'DOOM DATASETS',CLASS=A,MSGCLASS=X
//ALLOCATE EXEC PGM=IEFBR14
//STATE    DD DSN=DOOM.STATE,DISP=(NEW,CATLG),
//            UNIT=3380,SPACE=(TRK,(1,1)),
//            DCB=(RECFM=FB,LRECL=80,BLKSIZE=3200)
//ENTITIES DD DSN=DOOM.ENTITIES,DISP=(NEW,CATLG),
//            UNIT=3380,SPACE=(TRK,(10,10)),
//            DCB=(RECFM=FB,LRECL=120,BLKSIZE=3600)
//COMMANDS DD DSN=DOOM.COMMANDS,DISP=(NEW,CATLG),
//            UNIT=3380,SPACE=(TRK,(5,5)),
//            DCB=(RECFM=FB,LRECL=80,BLKSIZE=3200)
//TACTICS  DD DSN=DOOM.TACTICS,DISP=(NEW,CATLG),
//            UNIT=3380,SPACE=(TRK,(5,5)),
//            DCB=(RECFM=FB,LRECL=100,BLKSIZE=3000)
```

## Bridge Service Components

### 1. State Extractor (Python)
```python
# doom_state_extractor.py
import psutil
import struct
import ftplib
import time

class DoomStateExtractor:
    def __init__(self, mvs_host, mvs_user, mvs_pass):
        self.mvs_ftp = ftplib.FTP(mvs_host, mvs_user, mvs_pass)
        self.doom_pid = self.find_doom_process()
        
    def extract_player_state(self):
        # Read DOOM memory for player struct
        # Convert to EBCDIC and fixed-width format
        # Upload to MVS as DOOM.STATE
        pass
        
    def extract_visible_entities(self):
        # Scan thing list in DOOM memory
        # Format as COBOL records
        # Upload to MVS as DOOM.ENTITIES
        pass
```

### 2. Input Bridge (Python)
```python
# doom_input_bridge.py
import pyautogui
import ftplib
from Xlib import X, display

class DoomInputBridge:
    def __init__(self, mvs_host):
        self.display = display.Display()
        self.doom_window = self.find_doom_window()
        
    def process_commands(self):
        # Download DOOM.COMMANDS from MVS
        # Parse COBOL command records
        # Send inputs to DOOM window
        pass
```

## COBOL Integration Updates

### New COPYBOOK for Docker Environment
```cobol
      * DOOMENV.CPY - Environment settings for Docker z/OS
       01  DOOM-ENVIRONMENT.
           05  BRIDGE-STATUS    PIC X.      * A=Active, I=Inactive
           05  LAST-SYNC-TIME   PIC 9(8).  * HHMMSSSS
           05  SYNC-LATENCY     PIC 9(4).  * Milliseconds
           05  DOCKER-HOST      PIC X(15). * IP address
           05  DOOM-PROCESS-ID  PIC 9(5).
```

## Timing and Synchronization

### Challenge: JCL Batch vs Real-time DOOM
- DOOM runs at 35 FPS (28.5ms per frame)
- JCL job submission overhead: ~100-500ms
- FTP transfer time: ~50-100ms per file

### Solution: Buffered Command Queue
1. COBOL writes multiple commands per job
2. Bridge buffers and executes at proper timing
3. State updates batched every 10 frames (~285ms)

## Development Workflow

### 1. Start Docker Environment
```bash
docker-compose up -d
```

### 2. Submit Initial JCL
```bash
# Copy JCL to MVS via FTP
ftp mvs-host < submit-doom-init.ftp
```

### 3. Start Bridge Service
```bash
python bridge/doom_bridge.py --mvs-host localhost
```

### 4. Launch DOOM
```bash
# Start DOOM with specific window title for detection
DOOM -window -geometry 640x480
```

### 5. Monitor Execution
- Watch MVS job output via TN3270
- Bridge logs show state sync
- DOOM responds to COBOL commands!

## Performance Optimizations

1. **Parallel Job Submission**: Use multiple initiators
2. **Dataset Buffering**: Pre-allocate multiple generations
3. **Binary Transfer Mode**: Reduce FTP overhead
4. **Memory Mapped Files**: Fast host-side state sharing

## Security Considerations

1. Docker container isolated from host
2. FTP credentials in environment variables
3. Limited network exposure (localhost only)
4. No direct MVS-to-internet connection

## Next Implementation Steps

1. Set up Hercules Docker container
2. Create MVS datasets and COBOL programs
3. Implement basic state extractor
4. Test simple movement commands
5. Add combat capabilities