# DOOM-COBOL Complete Flow Diagram

## Live Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DOOM Process (Modified)                            │
│  ┌─────────────┐                                                           │
│  │  Game Loop  │──▶ Every tick: X_ExportState()                           │
│  └─────────────┘                                                           │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────┐    ┌──────────────────────────┐  │
│  │  UDP Packet (Port 31337)            │    │ /tmp/doom_state.dat      │  │
│  │  • Magic: 'DOOM'                    │    │ • COBOL 80-byte format   │  │
│  │  • Player pos, health, ammo         │    │ • STATE/PLAYER/AMMO/ENEMY│  │
│  │  • Enemy positions & health         │    │ • ASCII text file        │  │
│  │  • Binary format                    │    └──────────────────────────┘  │
│  └─────────────────────────────────────┘                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                                    │
                    ▼                                    │
┌─────────────────────────────────────────┐             │
│     SQLite Capture (Port 31337)         │             │
│  ┌─────────────────────────────────┐   │             │
│  │ doom_state_sqlite.py             │   │             │
│  │ • Receives UDP packets           │   │             │
│  │ • Parses binary data             │   │             │
│  │ • Stores in SQLite tables        │   │             │
│  │ • Also writes COBOL format       │───┘             │
│  └─────────────────────────────────┘                  │
│                                                        │
│  Database Schema:                                      │
│  • game_state (tick, health, x, y, ...)               │
│  • enemies (type, health, distance)                   │
│  • cobol_state (80-byte records)                      │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│    MVS Dataset Converter                │
│  ┌─────────────────────────────────┐   │
│  │ gamestate_to_mvs.py             │   │
│  │ • Monitors SQLite for new states │   │
│  │ • Converts to MVS format         │   │
│  │ • RECFM=FB LRECL=80             │   │
│  │ • Creates EBCDIC datasets        │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Output Files:                          │
│  • mvs_datasets/DOOM.GAMESTAT          │
│  • mvs_datasets/DOOM.GAMESTAT.ASCII    │
│  • mvs_datasets/GAMESTAT.CURRENT       │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│      MVS FTP Gateway (Port 2121)        │
│  ┌─────────────────────────────────┐   │
│  │ mvs_ftp_gateway.py               │   │
│  │ • FTP server for z/OS            │   │
│  │ • Serves GAMESTAT datasets       │   │
│  │ • Receives COMMANDS datasets     │   │
│  │ • EBCDIC/ASCII conversion        │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
                    │
                    ▼ FTP
┌─────────────────────────────────────────┐
│         z/OS Mainframe                  │
│  ┌─────────────────────────────────┐   │
│  │ JCL: DOOMAI2                     │   │
│  │ • FTP GET GAMESTAT.CURRENT       │   │
│  │ • Run COBOL program              │   │
│  │ • FTP PUT COMMANDS.NEW           │   │
│  └─────────────────────────────────┘   │
│                 │                       │
│                 ▼                       │
│  ┌─────────────────────────────────┐   │
│  │ COBOL: DOOMAI2.COB              │   │
│  │ • Reads game state records       │   │
│  │ • AI decision logic              │   │
│  │ • Writes command records         │   │
│  └─────────────────────────────────┘   │
│                                         │
│  DOOM.COMMANDS Output:                  │
│  COMMAND MOVE    FORWARD 0020...        │
│  COMMAND TURN    RIGHT   0045...        │
│  COMMAND SHOOT           0003...        │
└─────────────────────────────────────────┘
                    │
                    ▼ FTP
┌─────────────────────────────────────────┐
│    FTP Action Reader                    │
│  ┌─────────────────────────────────┐   │
│  │ ftp_action_reader.py             │   │
│  │ • Monitors DOOM.COMMANDS file    │   │
│  │ • Parses 80-byte records         │   │
│  │ • Converts to DOOM format        │   │
│  │ • Queues for processing          │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│   Web Server (Port 8080)                │
│  ┌─────────────────────────────────┐   │
│  │ cobol_action_server.py           │   │
│  │ • HTTP API for actions           │   │
│  │ • Real-time web interface        │   │
│  │ • /api/actions/* endpoints       │   │
│  │ • NO DOOM INPUT YET (Step 9)     │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Data Formats

### UDP State Packet (Binary)
```c
struct {
    uint32_t magic;     // 'DOOM'
    uint32_t version;   // 1
    uint32_t tick;      // Game tick
    int32_t health;     // Player health
    int32_t armor;      // Player armor
    int32_t bullets;    // Ammo counts...
    int32_t x, y, z;    // Position (fixed point)
    uint32_t angle;     // BAM units
    // ... enemies follow
}
```

### COBOL Dataset Record (80 bytes ASCII/EBCDIC)
```
Columns 1-80:
STATE   00001234012025010100000...
PLAYER  +0001024+0001024+0000000...
AMMO    005000200100004020000000...
ENEMY   09100+0001200+0001100002...
```

### COBOL Command Record (80 bytes)
```
Columns 1-80:
COMMAND MOVE    FORWARD 00209SURVIVAL RETREAT...
        │       │       │    │
        Action  Direct  Value Priority/Reason
```

## Running the Demo

```bash
# Full interactive demo showing all components
./demo_full_flow.sh

# The demo will:
# 1. Check/build modified DOOM
# 2. Start SQLite capture 
# 3. Start MVS converter
# 4. Start FTP gateway
# 5. Start web server
# 6. Launch DOOM
# 7. Show live monitoring

# While running, press:
# [s] - SQLite stats
# [d] - Recent game states  
# [m] - MVS datasets
# [c] - Simulate COBOL commands
# [q] - Quit
```

## What You'll See

1. **DOOM Window**: Game running with state export
2. **Terminal**: Live monitoring of data flow
3. **Web Browser** (http://localhost:8080): COBOL commands appearing
4. **Database**: Growing with game states
5. **Files**: MVS datasets being created/updated

## Key Points

- Game state exported 35 times per second
- Each state becomes multiple 80-byte COBOL records
- FTP gateway ready for real mainframe connection
- Web API shows commands but doesn't send to DOOM yet
- Everything designed for z/OS COBOL processing