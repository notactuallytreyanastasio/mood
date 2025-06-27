# DOOM State Introspection Design

## Overview
This document outlines the design for extracting real-time game state from a running DOOM instance and converting it into COBOL-processable data structures.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   DOOM Process  │────▶│ State Extractor  │────▶│  COBOL Dataset  │
│   (Running)     │     │  (Python/C++)    │     │  (MVS Format)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                         │
         │                       ▼                         │
         │              ┌──────────────────┐              │
         │              │   Input Bridge   │              │
         │◀─────────────│ (Keyboard/Mouse) │◀─────────────┘
                        └──────────────────┘
```

## State Extraction Methods

### Option 1: Memory Reading (Linux/Windows)
- Use process memory inspection to read DOOM's internal state
- Target key data structures:
  - Player position (x, y, z coordinates)
  - Player angle/direction
  - Health, armor, ammo counts
  - Monster positions and types
  - Item locations
  - Map geometry in current area

### Option 2: Screen Capture Analysis
- Capture DOOM's frame buffer
- Use computer vision to identify:
  - HUD elements (health, ammo, armor)
  - Visible enemies
  - Walls and obstacles
  - Items and pickups
- Less precise but more portable

### Option 3: DOOM Source Modification
- Add a network interface to DOOM source
- Stream game state over TCP/UDP
- Most accurate but requires custom DOOM build

## COBOL Data Structures

### Game State Master Record (DOOM.STATE)
```cobol
01  DOOM-STATE-RECORD.
    05  GAME-TICK           PIC 9(9) COMP.
    05  PLAYER-DATA.
        10  PLAYER-X        PIC S9(9) COMP.
        10  PLAYER-Y        PIC S9(9) COMP.
        10  PLAYER-Z        PIC S9(9) COMP.
        10  PLAYER-ANGLE    PIC S9(3) COMP.
        10  PLAYER-HEALTH   PIC 9(3) COMP.
        10  PLAYER-ARMOR    PIC 9(3) COMP.
        10  PLAYER-AMMO     OCCURS 6 TIMES PIC 9(3) COMP.
        10  CURRENT-WEAPON  PIC 9 COMP.
    05  MAP-SECTION.
        10  CURRENT-LEVEL   PIC 99 COMP.
        10  CURRENT-AREA    PIC X(8).
```

### Visible Entities File (DOOM.ENTITIES)
```cobol
01  ENTITY-RECORD.
    05  ENTITY-TYPE         PIC X.      * M=Monster, I=Item, D=Door
    05  ENTITY-SUBTYPE      PIC 99.     * Specific monster/item ID
    05  ENTITY-X            PIC S9(9) COMP.
    05  ENTITY-Y            PIC S9(9) COMP.
    05  ENTITY-Z            PIC S9(9) COMP.
    05  ENTITY-DISTANCE     PIC 9(5) COMP.
    05  ENTITY-ANGLE        PIC S9(3) COMP.
    05  ENTITY-HEALTH       PIC 9(3) COMP.
    05  ENTITY-STATE        PIC X.      * A=Active, D=Dead, I=Idle
```

### Tactical Analysis Output (DOOM.TACTICS)
```cobol
01  TACTICAL-RECORD.
    05  THREAT-LEVEL        PIC 9.      * 0-9 scale
    05  PRIMARY-TARGET.
        10  TARGET-TYPE     PIC X.
        10  TARGET-X        PIC S9(9) COMP.
        10  TARGET-Y        PIC S9(9) COMP.
        10  TARGET-ANGLE    PIC S9(3) COMP.
    05  MOVEMENT-RECOMMENDATION.
        10  MOVE-DIRECTION  PIC X.      * N,S,E,W,X(none)
        10  MOVE-URGENCY    PIC 9.      * 0-9 scale
    05  ACTION-QUEUE        OCCURS 5 TIMES.
        10  ACTION-CODE     PIC XX.     * MV,FR,RL,OP,PK
        10  ACTION-PARAM    PIC S9(3) COMP.
```

## State Extraction Process

### Phase 1: Memory Map Discovery
1. Identify DOOM process
2. Map memory regions
3. Locate key data structures (player struct, thing list, etc.)
4. Create offset table for reliable access

### Phase 2: Real-time Extraction
1. Read memory at 35Hz (DOOM's tick rate)
2. Extract player state
3. Scan thing list for monsters/items
4. Calculate relative positions and angles
5. Write to staging files

### Phase 3: COBOL Processing
1. JCL job reads staging files
2. COBOL programs analyze state
3. Tactical decisions made
4. Commands written to output queue

## Input Bridge Design

### Command Queue (DOOM.COMMANDS)
```cobol
01  COMMAND-RECORD.
    05  COMMAND-TYPE        PIC X.      * K=Key, M=Mouse
    05  COMMAND-ACTION      PIC X.      * P=Press, R=Release
    05  COMMAND-CODE        PIC X(4).   * Key code or mouse button
    05  MOUSE-DELTA-X       PIC S9(3) COMP.
    05  MOUSE-DELTA-Y       PIC S9(3) COMP.
```

### Input Bridge Process
1. Read command queue from COBOL output
2. Translate to X11/Windows events
3. Send to DOOM window
4. Clear processed commands

## Implementation Phases

### Phase 1: Proof of Concept
- Simple memory reader for player position
- Basic COBOL program to track movement
- Keyboard input for WASD movement only

### Phase 2: Combat Capability
- Extract monster positions
- Implement DOOMAIM.COB for targeting
- Add mouse control for aiming
- Fire weapon commands

### Phase 3: Full Autonomy
- Complete state extraction
- Pathfinding in COBOL
- Tactical decision making
- Item collection logic

## Technical Considerations

1. **Timing**: DOOM runs at 35 FPS, JCL jobs need sub-second execution
2. **Precision**: Fixed-point arithmetic in COBOL for angles/positions
3. **Latency**: Minimize delay between state read and command execution
4. **Reliability**: Handle DOOM crashes/restarts gracefully

## Next Steps
1. Implement basic memory reader in C/Python
2. Create COBOL copybooks for data structures
3. Write test JCL to verify data flow
4. Build minimal input bridge
5. Test with simple movement commands