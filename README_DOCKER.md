# DOOM-COBOL Docker Architecture

## Overview

The entire DOOM-COBOL system is now fully dockerized! This means you can run a mainframe, bridge service, and control interface all in containers, orchestrated by docker-compose.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Host System                              │
├─────────────────────┬────────────────┬─────────────────────────┤
│   DOOM Process      │ Docker Network │   User Interface        │
│   (Native)          │   172.20.0.0/16│                         │
│                     │                 │  ┌──────────────────┐  │
│                     │ ┌─────────────┐ │  │ Web Browser      │  │
│                     │ │ Mainframe   │ │  │ localhost:8080   │  │
│                     │ │ Container   │ │  └────────┬─────────┘  │
│                     │ │ z/OS MVS    │ │           │            │
│                     │ └──────┬──────┘ │  ┌────────▼─────────┐  │
│  ┌─────────────┐   │        │        │  │ COBOL Interface  │  │
│  │ DOOM.EXE    │◀──┼────────┼────────┼──│ localhost:9999   │  │
│  └─────────────┘   │ ┌──────▼──────┐ │  └──────────────────┘  │
│                     │ │   Bridge    │ │                         │
│                     │ │  Container  │ │  ┌──────────────────┐  │
│                     │ └─────────────┘ │  │ TN3270 Terminal  │  │
│                     │                 │  │ localhost:3270   │  │
│                     └─────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Start Everything
```bash
make up
```

This single command:
- Builds all Docker images
- Starts the mainframe emulator
- Launches the bridge service
- Starts the COBOL interface
- Launches the web UI

### 2. Start DOOM
```bash
# Any DOOM version works:
chocolate-doom -window -geometry 640x480
# or
gzdoom -window -width 640 -height 480
# or
doom.exe (in DOSBox)
```

### 3. Control DOOM

#### Option A: Web UI
Open http://localhost:8080 in your browser

#### Option B: Command Line
```bash
# Send individual commands
echo "MOVE FORWARD" | nc localhost 9999
echo "TURN RIGHT 90" | nc localhost 9999
echo "SHOOT" | nc localhost 9999

# Or use the Makefile shortcuts
make cmd-"MOVE FORWARD"
make cmd-"TURN RIGHT 45"
make cmd-"SHOOT 3"
```

#### Option C: Direct COBOL
Connect to the mainframe via TN3270 and submit JCL jobs directly

## Services

### 1. Mainframe Container (port 3270, 2121)
- Runs Hercules emulator with MVS 3.8j
- Hosts COBOL programs and JCL jobs
- Provides FTP access for dataset transfer

### 2. Bridge Container (host network)
- Reads DOOM process memory
- Uploads game state to MVS datasets
- Downloads commands from COBOL
- Sends keyboard/mouse input to DOOM

### 3. COBOL Interface Container (port 9999)
- TCP server for simple command submission
- Translates high-level commands to COBOL records
- Manages MVS dataset communication

### 4. Web UI Container (port 8080)
- Real-time system status dashboard
- Command buttons for easy control
- Game state visualization
- Command history

## Command Reference

### Movement Commands
```
MOVE FORWARD [duration]   # Move forward for duration seconds
MOVE BACK [duration]      # Move backward
MOVE LEFT [duration]      # Strafe left
MOVE RIGHT [duration]     # Strafe right
```

### Combat Commands
```
SHOOT [count]             # Fire weapon count times
TURN LEFT [degrees]       # Turn left by degrees
TURN RIGHT [degrees]      # Turn right by degrees
USE                       # Open doors/activate switches
```

### Weapon Commands
```
WEAPON 1                  # Switch to fist
WEAPON 2                  # Switch to pistol
WEAPON 3                  # Switch to shotgun
WEAPON 4                  # Switch to chaingun
WEAPON 5                  # Switch to rocket launcher
WEAPON 6                  # Switch to plasma gun
WEAPON 7                  # Switch to BFG9000
```

### System Commands
```
STATUS                    # Get current game state
RUN jobname              # Submit custom JCL job
```

## Advanced Usage

### Custom JCL Jobs
Create custom JCL in `cobol-interface/templates/` and run with:
```bash
echo "RUN MYCUSTOMJOB" | nc localhost 9999
```

### Monitoring
```bash
# View all logs
make logs

# View specific service logs
make logs-mainframe
make logs-bridge
make logs-cobol-interface

# Check system health
curl http://localhost:8080/api/status | jq
```

### Debugging
```bash
# Access mainframe console
docker exec -it doom-mainframe bash

# Check MVS datasets
ftp localhost 2122
> dir 'DOOM.*'

# View bridge status
docker logs doom-bridge -f
```

## Configuration

### Environment Variables
Create a `.env` file to customize:
```env
# DOOM process name to find
DOOM_PROCESS_NAME=chocolate-doom

# Logging level
LOG_LEVEL=DEBUG

# Bridge update rate
BRIDGE_TICK_RATE=10

# MVS credentials
MVS_USER=HERC01
MVS_PASS=CUL8TR
```

### Scaling Performance
Edit `docker-compose.yml` to adjust:
- Container resource limits
- Update frequencies
- Buffer sizes

## Troubleshooting

### "DOOM process not found"
- Ensure DOOM is running with correct window title
- Set `DOOM_PROCESS_NAME` environment variable

### "Cannot connect to COBOL interface"
```bash
# Check if service is running
docker ps | grep cobol-interface

# Test connectivity
telnet localhost 9999
```

### "No game state updates"
- Verify bridge has access to DOOM process
- Check bridge logs: `make logs-bridge`
- Ensure X11 forwarding works (Linux)

## The Magic

When you send a command like "SHOOT":
1. COBOL Interface receives TCP command
2. Converts to EBCDIC COBOL record
3. FTPs to MVS dataset DOOM.COMMANDS
4. JCL job DOOMTACT reads command
5. COBOL program analyzes game state
6. Outputs mouse/keyboard commands
7. Bridge reads commands from MVS
8. Sends input events to DOOM
9. DOOM responds to input!

All orchestrated by Docker, because even mainframes deserve containers.

## Stop Everything
```bash
make down
```

## Clean Up
```bash
make clean
```

This removes all containers, volumes, and Docker artifacts.

## Next Steps

1. Implement more sophisticated COBOL AI
2. Add multiplayer support (multiple DOOM instances)
3. Create CICS transactions for real-time control
4. Build RESTful API over COBOL programs
5. Kubernetes deployment for cloud mainframe gaming!

Remember: If it's worth doing, it's worth overdoing with enterprise technology.