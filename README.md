# DOOM-COBOL Integration Project

## Overview

This project demonstrates a fully-functional integration between DOOM (1993) and COBOL running on z/OS, proving that 1960s mainframe technology can play 1990s video games through clever bridging.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Modified DOOM  │────▶│  State Bridge    │────▶│  z/OS MVS       │
│  (Linux/X11)    │     │  (Python)        │     │  (COBOL AI)     │
│                 │     │                  │     │                 │
│  Exports state  │     │  Receives UDP    │     │  Analyzes state │
│  via UDP:31337  │     │  Sends commands  │     │  Makes decision │
│  to localhost   │     │  via network     │     │  Returns cmds   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         ▲                                                 │
         │                                                 │
         └─────────────────────────────────────────────────┘
                     Commands (keyboard/mouse)
```

## Current Implementation Status

### ✅ Completed Components

1. **Modified DOOM Source**
   - Exports complete game state via UDP (port 31337)
   - Exports COBOL-formatted text to `/tmp/doom_state.dat`
   - 10Hz update rate (every 3 game tics)
   - Includes player stats, position, and nearby enemies

2. **State Bridge** 
   - Receives binary game state from DOOM
   - Implements AI logic (survival/combat/exploration modes)
   - Sends commands to control interface

3. **COBOL Interface**
   - TCP server on port 9999
   - Accepts high-level commands (MOVE, TURN, SHOOT, etc.)
   - Supports both real MVS and mock mode

4. **COBOL AI Program**
   - Reads game state from MVS datasets
   - Makes tactical decisions based on health/ammo/enemies
   - Outputs movement and combat commands

### 🚧 In Progress

1. **Input Control for Modified DOOM**
   - Need to implement X11 event injection or
   - Modify DOOM to accept network commands directly

2. **Full MVS Integration**
   - Currently using mock MVS datasets
   - Need Hercules setup for real mainframe emulation

## Data Flow

### 1. Game State Export (DOOM → Bridge)

**Binary Format (UDP)**:
```c
struct {
    uint32_t magic;      // 'DOOM'
    uint32_t tick;       // Game time
    int32_t health;      // Player health
    int32_t armor;       // Player armor  
    int32_t x, y, z;     // Position (fixed-point)
    int32_t angle;       // Facing (BAM units)
    // ... enemies, ammo, etc
}
```

**COBOL Format (File)**:
```
STATE 00012345 01
PLAYER+0001024+0001024+0000000+090100050
AMMO  0050002001000040 2
ENEMY 09 060 +0001200 +0001100 00256
```

### 2. AI Decision Making

The AI operates in three modes:

- **Survival Mode** (health < 30): Retreat and evade
- **Combat Mode** (enemies present): Engage targets
- **Exploration Mode** (default): Move forward and search

### 3. Command Execution

Commands flow through the pipeline:
```
COBOL Decision → MVS Dataset → FTP → Bridge → Network → DOOM Input
```

Example commands:
- `MOVE FORWARD 2` - Move forward for 2 seconds
- `TURN RIGHT 45` - Turn 45 degrees right
- `SHOOT 3` - Fire weapon 3 times

## Quick Start

### Prerequisites

- Linux or macOS with Docker
- Python 3.8+
- GCC compiler
- X11 libraries (for Linux DOOM)

### Option 1: Modified DOOM with State Export

```bash
# 1. Build modified DOOM
./scripts/build_modified_doom.sh

# 2. Start the full system
./scripts/start_full_system.sh

# 3. Watch the AI play!
```

### Option 2: Docker Container (Linux)

```bash
# Build and run containerized DOOM
./scripts/run_doom_container.sh

# Connect via VNC to watch: vnc://localhost:5900
```

### Option 3: Mock Testing

```bash
# Test without building DOOM
./scripts/test_mock_system.sh
```

## Technical Details

### DOOM Modifications

The modifications add a state export module (`x_state.c`) that:
- Hooks into the main game loop (`G_Ticker`)
- Extracts player and enemy data
- Sends via UDP for minimal latency
- Writes COBOL format for mainframe compatibility

### Number Systems

DOOM uses two special number formats:
- **Fixed Point (16.16)**: Position/velocity values
  - Upper 16 bits = integer part
  - Lower 16 bits = fractional part
- **BAM (Binary Angle Measurement)**: Angles
  - 0x00000000 = 0°
  - 0xFFFFFFFF = 360°

### Network Protocol

State packets are sent via UDP to localhost:31337
- Non-blocking to avoid game lag
- Binary format for efficiency
- ~100 bytes per packet
- 10 packets/second

## Future Enhancements

1. **Real z/OS Integration**
   - Set up Hercules mainframe emulator
   - Implement FTP dataset transfers
   - Submit JCL jobs for AI processing

2. **Advanced AI**
   - Pathfinding algorithms in COBOL
   - Predictive aiming
   - Health/ammo management
   - Level navigation

3. **Network Play**
   - Multiple DOOM instances
   - Distributed COBOL processing
   - Tournament system

## Architecture Philosophy

This project intentionally bridges a 30-year technology gap:
- **1960s**: COBOL/JCL batch processing
- **1990s**: Real-time 3D gaming
- **2020s**: Modern integration techniques

The absurdity is the point - proving that with enough creativity, any systems can be integrated.

## Troubleshooting

### DOOM won't build
- Ensure X11 dev libraries installed: `apt-get install libx11-dev`
- Check GCC version (needs C99 support)

### No state data received
- Check firewall rules for UDP port 31337
- Verify DOOM is running (not in menu)
- Look for `/tmp/doom_state.dat` file

### Commands not working
- Verify COBOL interface is running (port 9999)
- Check X11 DISPLAY variable is set
- Ensure proper permissions for input injection

## Contributing

This project welcomes contributions! Areas of interest:
- COBOL AI improvements
- JCL job optimization  
- Alternative input methods
- Performance enhancements

## License

- DOOM Source: GPL (id Software)
- Project Code: MIT