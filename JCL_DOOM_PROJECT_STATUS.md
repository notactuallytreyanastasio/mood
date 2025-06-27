# JCL DOOM Project Status & Vision

## Current Status

We've created a proof-of-concept for running DOOM as a JCL-based state machine:

### What We Built
1. **JCL Job Chain Architecture** - Each game "tick" is a batch job that:
   - Reads game state from MVS datasets
   - Processes one action (movement, combat, etc.)
   - Renders ASCII output
   - Chains to the next job via INTRDR submission

2. **COBOL Game Logic** - Programs that handle:
   - ASCII rendering (DOOMREND.COB)
   - Movement and collision (DOOMMV.COB)
   - State persistence in datasets

3. **Turn-Based DOOM** - Transformed real-time FPS into batch-processed turns

## The New Vision: JCL as Orchestration Layer

### Conceptual Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   Real DOOM     │────▶│  MCP Server  │────▶│ JCL/COBOL   │
│   (Running)     │◀────│  (Translator)│◀────│ State Engine│
└─────────────────┘     └──────────────┘     └─────────────┘
       ▲                                              │
       │                                              │
       └──────────────────────────────────────────────┘
                    Command Loop
```

### Key Components Needed

1. **MCP (Model Context Protocol) Server**
   - Understands DOOM's visual output (screen capture/memory reading)
   - Translates game state to COBOL-readable format
   - Sends keyboard/mouse commands to DOOM
   - Acts as bridge between batch and real-time worlds

2. **Enhanced COBOL Programs**
   - **DOOMAIM.COB** - Calculates aim angles based on enemy positions
   - **DOOMPATH.COB** - A* pathfinding in COBOL
   - **DOOMTACT.COB** - Tactical decision making (when to shoot, dodge, etc.)
   - **DOOMWEAP.COB** - Weapon selection logic

3. **JCL Orchestration Layer**
   - Jobs that represent high-level strategies
   - Conditional execution based on game state
   - Multi-step tactical sequences (e.g., "clear room" procedure)

### The Wild Part: Full State Externalization

The goal is to have JCL/COBOL completely drive DOOM by:

1. **State Extraction**
   - MCP server reads DOOM's frame buffer or memory
   - Identifies: enemies, walls, items, player status
   - Converts to structured data in MVS datasets

2. **Decision Making in Batch**
   - JCL jobs analyze state and decide strategy
   - COBOL programs calculate exact movements/aims
   - Return codes determine next action sequence

3. **Action Injection**
   - MCP server receives commands from COBOL
   - Translates to keyboard/mouse inputs
   - Feeds them to running DOOM instance

### Example Flow

```
1. DOOMREAD.JCL runs → MCP captures DOOM screen → Updates DOOM.GAMESTATE
2. DOOMEVAL.JCL runs → Analyzes threats → RC=20 (enemy detected)
3. DOOMCMBT.JCL runs → Calls DOOMAIM.COB → Calculates angle to enemy
4. DOOMFIRE.JCL runs → Sends "aim(x,y) + shoot" to MCP → DOOM fires
5. Loop back to step 1
```

### The Absurd Beauty

- **Mainframe AI playing DOOM** - COBOL programs making tactical decisions
- **Batch processing real-time game** - Each frame analyzed by job submission
- **1960s tech controlling 1993 game** - Ultimate retro-computing
- **JCL as game strategy language** - IF/THEN/ELSE via COND codes

### Technical Challenges to Solve

1. **Frame Synchronization** - Matching batch job speed to game speed
2. **State Representation** - Encoding 3D world in flat files
3. **Precision Timing** - DOOM needs quick reactions, JCL is... not quick
4. **MCP Server Development** - Building the bridge between worlds

### Next Steps for Implementation

1. Build MCP server that can read DOOM state
2. Expand COBOL library with combat/navigation algorithms  
3. Create JCL procedure library for common tactics
4. Test with DOOM running in slow-motion initially
5. Optimize job submission for "playable" speed

## The Ultimate Goal

A fully functional system where IBM mainframe technology from the 1960s-70s autonomously plays DOOM through batch job submissions, with all game logic and decision-making happening in COBOL programs orchestrated by JCL scripts. 

It's beautifully absurd - taking the most real-time, reflex-based game and making it run through the most batch-oriented, business-focused technology stack imaginable.

Ready to let me cook with --dangerously-skip-permissions? This is going to be legendary.