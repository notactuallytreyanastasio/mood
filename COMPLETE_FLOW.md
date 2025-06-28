# DOOM-COBOL Complete Flow (Steps 1-8)

## Overview

We have successfully implemented Steps 1-8 of the DOOM-COBOL integration. The system can now:

1. ✅ Build/find modified DOOM with state export
2. ✅ Capture game state to SQLite database
3. ✅ Design COBOL structures for game data
4. ✅ Map COBOL structures completely
5. ✅ Map state to COBOL AI decisions
6. ✅ Write COBOL actions to FTP datasets
7. ✅ Read actions from FTP gateway
8. ✅ Serve actions via web API (without DOOM input)

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Modified DOOM  │────▶│  SQLite Database │────▶│  MVS Formatter   │
│  (State Export) │ UDP │  (Game States)   │     │ (COBOL Datasets) │
└─────────────────┘     └──────────────────┘     └──────────────────┘
                                                           │
                                                           ▼
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Web Server    │◀────│   FTP Gateway    │◀────│   z/OS + COBOL   │
│  (Action API)   │     │  (MVS Datasets)  │ FTP │   (AI Logic)     │
└─────────────────┘     └──────────────────┘     └──────────────────┘
        │
        ▼
   HTTP API
 (No DOOM input yet)
```

## Component Details

### 1. Modified DOOM (`build_system/`)
- `setup_doom.sh` - Builds DOOM with state export patches
- `doom-state-export.patch` - Adds UDP state broadcasting
- Exports game state on port 31337 every tick

### 2. State Capture (`build_system/`)
- `doom_state_sqlite.py` - Captures UDP packets to SQLite
- `cobol_mapper.py` - Maps SQLite to 80-byte COBOL records
- `gamestate_to_mvs.py` - Creates MVS datasets for FTP

### 3. COBOL Programs (`cobol/`)
- `DOOMAI2.COB` - Enhanced AI that reads full game state
- `DOOMSTAT.CPY` - Complete copybook with all structures
- Makes tactical decisions based on health/ammo/enemies

### 4. JCL Jobs (`jcl/`)
- `COMPILE2.JCL` - Compiles DOOMAI2 with copybook
- `DOOMAI2.JCL` - Runs AI with FTP GET/PUT

### 5. FTP Gateway (`ftp-gateway/`)
- `mvs_ftp_gateway.py` - FTP server understanding MVS datasets
- Handles EBCDIC/ASCII conversion
- Serves GAMESTAT, receives COMMANDS

### 6. Action Processing (`build_system/`)
- `ftp_action_reader.py` - Monitors for COBOL commands
- Parses 80-byte DOOM-COMMAND-RECORD format
- Converts to DOOM input format

### 7. Web Server (`web-ui/`)
- `cobol_action_server.py` - HTTP API for actions
- Real-time web interface
- REST endpoints for integration

## Running the System

### Quick Test
```bash
# Test the complete flow (without real mainframe)
./test_cobol_flow.sh
```

### Full System
```bash
# Terminal 1: Start FTP Gateway
python3 ftp-gateway/mvs_ftp_gateway.py

# Terminal 2: Start game state converter
python3 build_system/gamestate_to_mvs.py --monitor

# Terminal 3: Start web server
python3 web-ui/cobol_action_server.py

# Terminal 4: Start DOOM with state capture
./master_control.sh

# On z/OS: Submit DOOMAI2 job
```

## API Endpoints

- `GET /` - Web interface with real-time updates
- `GET /api/status` - System status
- `GET /api/actions/recent` - Recent actions (last 20)
- `GET /api/actions/all` - All actions in history
- `GET /api/actions/latest` - Most recent action
- `GET /api/actions/poll` - Long-poll for new actions

## Example Commands from COBOL

```
COMMAND MOVE    FORWARD 00209SURVIVAL RETREAT
COMMAND TURN    RIGHT   00453SECONDARY ACTION
COMMAND SHOOT           00015COMBAT ENGAGEMENT
COMMAND WAIT            00107NO ACTION DETERMINED
```

## Dataset Formats

### Input: DOOM.GAMESTAT (from DOOM)
```
STATE   00001234012025010100000...  (Game tick, level, date)
PLAYER  +0001024+0001024+0000000...  (Position, angle, health)
AMMO    005000200100004020000000...  (Bullets, shells, etc)
ENEMY   09100+0001200+0001100002...  (Type, health, position)
```

### Output: DOOM.COMMANDS (from COBOL)
```
COMMAND MOVE    BACK    00209SURVIVAL RETREAT
COMMAND SHOOT           00015COMBAT ENGAGEMENT
```

## What's NOT Done Yet (Step 9)

Step 9 will connect the web server output to DOOM input:
- Send commands to DOOM via UDP port 31338
- Or use AppleScript/pyautogui for keyboard control
- Close the feedback loop for full autonomy

## Testing Without Mainframe

The system includes test modes:
1. `test_cobol_flow.sh` - Full flow simulation
2. Web server `--test` flag adds sample data
3. FTP gateway creates dummy datasets

## Next Steps

To complete Step 9:
1. Add UDP sender to web server
2. Connect to DOOM's network input port
3. Or integrate with existing keyboard control
4. Test full autonomous gameplay loop

The infrastructure is ready - we just need to connect the final piece!