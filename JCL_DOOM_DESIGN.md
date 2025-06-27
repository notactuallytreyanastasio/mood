# JCL DOOM - Game State Machine Design

## Core Concept
Each JCL job represents one "frame" or game tick. Jobs chain together based on return codes that represent player actions and game events.

## Architecture Overview

### 1. Job Naming Convention
- `DOOMTICK` - Main game loop job
- `DOOMMOVE` - Process movement
- `DOOMCMBT` - Combat processing
- `DOOMREND` - "Render" the ASCII view
- `DOOMSAVE` - Save game state
- `DOOMLOAD` - Load game state

### 2. Return Code Mapping
```
RC=0  - Continue normal game loop
RC=4  - Move North
RC=8  - Move South  
RC=12 - Move East
RC=16 - Move West
RC=20 - Fire weapon
RC=24 - Open door
RC=28 - Pick up item
RC=99 - Game Over
RC=100 - Exit Game
```

### 3. Dataset Structure
- `DOOM.GAMESTATE` - Current game state (player position, health, ammo)
- `DOOM.LEVEL001` - Level 1 map data
- `DOOM.MONSTERS` - Monster positions and states
- `DOOM.ITEMS` - Item locations
- `DOOM.RENDER` - ASCII "screen" output

### 4. Game Loop Flow
```
DOOMTICK -> Read Input Dataset
         -> Determine Action (set RC)
         -> COND=(RC,EQ,4) -> DOOMOVE (North)
         -> COND=(RC,EQ,8) -> DOOMOVE (South)
         -> etc...
         -> DOOMREND (render new view)
         -> Loop back to DOOMTICK
```

### 5. ASCII Rendering Example
```
+------------------+
|#####  D  ########|
|#   #     #      #|
|# @ #     # $$   #|
|#   ###D###      #|
|#                #|
|##################|
+------------------+
HP: 100  AMMO: 50
> NORTH/SOUTH/EAST/WEST/FIRE/USE
```

Legend:
- @ = Player
- D = Demon
- $ = Ammo/Items
- # = Wall
- D = Door

## Implementation Strategy

1. Start with basic movement in a simple room
2. Add collision detection via COBOL program
3. Implement monster AI using job scheduling
4. Add combat system with damage calculation
5. Create multiple levels using dataset switching