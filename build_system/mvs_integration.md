# MVS/z/OS Integration Architecture

## Overview

The DOOM-COBOL integration runs entirely on z/OS mainframe with FTP gateways for data transfer:

```
z/OS Mainframe                           Linux/Mac Host
+------------------+                     +------------------+
| JCL: DOOMAI2    |                     | Modified DOOM    |
|   |              |                     |   |              |
|   v              |                     |   v              |
| COBOL: DOOMAI2  |                     | UDP State Export |
|   |              |                     |   |              |
|   v              |                     |   v              |
| DOOM.GAMESTAT   |<----- FTP GET ------| SQLite DB        |
| (input dataset) |                     |   |              |
|   |              |                     |   v              |
|   v              |                     | MVS Dataset      |
| AI Processing   |                     | Formatter        |
|   |              |                     |                  |
|   v              |                     |                  |
| DOOM.COMMANDS   |------ FTP PUT ----->| Action Queue     |
| (output dataset)|                     |   |              |
+------------------+                     |   v              |
                                        | Web Service      |
                                        | (Step 8)         |
                                        +------------------+
```

## Components

### 1. z/OS Side (Mainframe)

**JCL Jobs:**
- `COMPILE2.JCL` - Compiles DOOMAI2.COB with DOOMSTAT copybook
- `DOOMAI2.JCL` - Executes the AI:
  - FTP GET game state from Linux/Mac
  - Run COBOL AI program
  - FTP PUT commands back

**COBOL Programs:**
- `DOOMAI2.COB` - Enhanced AI that reads full game state
- `DOOMSTAT.CPY` - Copybook defining all data structures

**Datasets:**
- `DOOM.GAMESTAT` - Input game state (RECFM=FB LRECL=80)
- `DOOM.COMMANDS` - Output commands (RECFM=FB LRECL=80)
- `DOOM.AILOG` - Processing log (RECFM=FB LRECL=80)

### 2. Linux/Mac Side (DOOM Host)

**Services:**
- `mvs_ftp_gateway.py` - FTP server that handles MVS datasets
- `gamestate_to_mvs.py` - Converts SQLite to MVS format
- `doom_state_sqlite.py` - Captures DOOM state to SQLite

**Data Flow:**
1. Modified DOOM exports state via UDP
2. SQLite captures and stores state
3. MVS converter creates EBCDIC dataset
4. FTP gateway serves dataset to mainframe
5. Mainframe processes and returns commands
6. Commands queued for web service (Step 8)

## Running the System

### On Linux/Mac:

```bash
# 1. Start MVS FTP Gateway
python3 ftp-gateway/mvs_ftp_gateway.py

# 2. Start game state converter
python3 build_system/gamestate_to_mvs.py --monitor

# 3. Start DOOM with state capture
./master_control.sh
```

### On z/OS:

```jcl
// Submit DOOMAI2 job
SUB 'DOOM.JCL(DOOMAI2)'
```

## Dataset Formats

### DOOM.GAMESTAT (Input)
```
Columns 1-80:
STATE   00001234012025010100000...  (State header)
PLAYER  +0001024+0001024+0000000...  (Player data)
AMMO    005000200100004020000000...  (Ammunition)
ENEMY   09100+0001200+0001100002...  (Enemy 1)
ENEMY   02075+0000800+0000900001...  (Enemy 2)
...
```

### DOOM.COMMANDS (Output)
```
Columns 1-80:
COMMAND MOVE    FORWARD 00209SURVIVAL RETREAT     ...
COMMAND TURN    RIGHT   00303SECONDARY ACTION    ...
```

## FTP Configuration

The JCL uses FTP with these parameters:
- Host: 192.168.1.100 (configure for your network)
- Port: 21 (or 2121 for test gateway)
- User: doom / doomguy
- Paths:
  - GET: /doom/gamestate/GAMESTAT.CURRENT
  - PUT: /doom/commands/COMMANDS.NEW

## Testing

Test without full DOOM:
```bash
# Create test gamestat
python3 build_system/gamestate_to_mvs.py --test

# Start FTP gateway
python3 ftp-gateway/mvs_ftp_gateway.py

# Manual FTP test
ftp localhost 2121
> user doom doomguy
> cd /doom/gamestate
> get GAMESTAT.CURRENT
```

## EBCDIC/ASCII Conversion

The system handles character encoding automatically:
- Game state: ASCII → EBCDIC for mainframe
- Commands: EBCDIC → ASCII for processing
- FTP TYPE A mode handles conversion

## Next Steps

After commands are received from mainframe:
1. Parse DOOM.COMMANDS dataset
2. Convert to action format
3. Queue for web service (Step 8)
4. Eventually connect to DOOM input (Step 9)