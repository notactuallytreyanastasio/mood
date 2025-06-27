# DOOM-COBOL Blog Post Notes

## The Absurd Beauty of Mainframe DOOM

### Project Evolution

#### Phase 1: ASCII DOOM in Pure JCL/COBOL
- Started with a turn-based ASCII renderer
- Each game tick was a batch job submission
- JCL return codes controlled player movement
- Proved that game logic could run on mainframe batch processing

#### Phase 2: The Crazy Pivot - Real DOOM, COBOL Brain
- Why stop at ASCII when we can control the REAL DOOM?
- COBOL becomes the AI brain for DOOM
- JCL orchestrates tactical decisions
- Batch processing meets real-time gaming

### Technical Architecture

#### The Stack That Shouldn't Work (But Does)
1. **DOOM (1993)** - Running natively on modern Linux/Windows
2. **z/OS in Docker** - Hercules emulator running MVS 3.8j
3. **Python Bridge Service** - The translator between worlds
4. **COBOL Programs** - The tactical brain
5. **JCL Jobs** - The strategy orchestrator

#### Data Flow
```
Real DOOM → Memory Introspection → Python → FTP → MVS Datasets
                                                         ↓
                                                   COBOL Analysis
                                                         ↓
Keyboard/Mouse ← Python Bridge ← FTP ← MVS Commands
```

### The COBOL Programs

#### DOOMAIM.COB - Ballistics Calculator
- Calculates angle to target using fixed-point math
- Accounts for monster movement prediction
- Returns precise mouse movements needed

#### DOOMPATH.COB - A* Pathfinding
- Implements A* algorithm in COBOL
- Uses MVS datasets as node storage
- Finds optimal path through level

#### DOOMTACT.COB - Tactical Decision Engine
- Evaluates threats
- Prioritizes targets
- Decides fight vs flight
- Pure business logic for demon management

### Why This Matters

1. **COBOL is Turing Complete** - If it can run a bank, it can run DOOM
2. **Batch Can Be Real-Time** - With enough optimization and clever buffering
3. **Legacy Tech + Modern Problems** - Bridging 60 years of computing
4. **Because We Can** - The best reason for any technical project

### Challenges Overcome

#### Timing Issues
- DOOM: 35 FPS (28ms/frame)
- JCL: 100-500ms job submission
- Solution: Command buffering and predictive execution

#### Data Representation
- 3D coordinates in EBCDIC
- Fixed-point arithmetic for angles
- Binary to text conversions everywhere

#### State Synchronization
- FTP latency between Docker and host
- Dataset locking issues
- Solved with double-buffering

### Best Moments

1. **First Successful Movement** - COBOL told DOOM to move forward, and it did!
2. **First Demon Kill** - DOOMAIM.COB calculated the perfect headshot
3. **The Pathfinding Miracle** - Watching COBOL navigate E1M1
4. **JCL Decision Trees** - Return codes creating combat strategies

### Code Snippets That Spark Joy

```cobol
* From DOOMAIM.COB - Calculate angle to demon
COMPUTE WS-ANGLE-RADIANS = FUNCTION ATAN(
    (DEMON-Y - PLAYER-Y) / (DEMON-X - PLAYER-X))
COMPUTE MOUSE-DELTA-X = WS-ANGLE-RADIANS * 1000
```

```jcl
//COMBAT   EXEC PGM=DOOMTACT
//STEPLIB  DD DSN=DOOM.LOADLIB,DISP=SHR
//STATE    DD DSN=DOOM.STATE,DISP=SHR
//TACTICS  DD DSN=DOOM.TACTICS,DISP=(NEW,PASS)
//*
//DECIDE   IF (COMBAT.RC EQ 20) THEN
//SHOOT    EXEC PGM=DOOMFIRE
//         ELSE
//RETREAT  EXEC PGM=DOOMRUN
//         ENDIF
```

### Philosophical Implications

This project proves that:
1. No technology is truly obsolete if you're creative enough
2. The boundaries between "business" and "gaming" tech are artificial
3. COBOL's survival isn't just about maintenance - it can innovate
4. Sometimes the most impractical projects teach the most

### What We Learned

1. **COBOL is surprisingly good at math** - Fixed-point trig works great
2. **JCL can express complex logic** - It's just very... verbose
3. **Mainframes can game** - Latency is solvable with clever design
4. **Python makes a great bridge** - Between any two impossible things

### Future Possibilities

- Multiplayer DOOM with multiple mainframes
- CICS transaction server for real-time combat
- DB2 for persistent player stats
- REXX scripts for custom weapon mods
- PL/I for performance-critical sections

### The Real Point

This isn't about whether you SHOULD use COBOL for gaming. It's about proving that you CAN. In an industry obsessed with the new and shiny, there's something beautiful about making the old and reliable do something completely unexpected.

COBOL has been processing transactions since 1959. Today, it's fragging demons. Tomorrow? Who knows. Maybe your neural net should be written in FORTRAN.

### Technical Takeaway

The bridge between modern and legacy systems doesn't have to be painful. With containers, clever protocols, and a sense of humor, you can make anything talk to anything. Even DOOM to COBOL.

### Sign-Off

"The only system more eternal than DOOM is COBOL." - Project motto

Built with love, JCL, and an inappropriate amount of caffeine.