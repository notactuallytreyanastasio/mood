      *================================================================
      * DOOMSTAT.CPY - DOOM Game State COBOL Copy Book
      * Complete data structure for DOOM-COBOL integration
      *================================================================
       
       01  DOOM-GAME-STATE.
           05  STATE-HEADER.
               10  STATE-RECORD-TYPE      PIC X(8).
                   88  VALID-STATE-REC    VALUE 'STATE   '.
               10  STATE-TICK             PIC 9(8).
               10  STATE-LEVEL            PIC 99.
               10  STATE-TIMESTAMP        PIC 9(8).
               10  FILLER                 PIC X(52).
           
           05  PLAYER-RECORD.
               10  PLAYER-RECORD-TYPE     PIC X(8).
                   88  VALID-PLAYER-REC   VALUE 'PLAYER  '.
               10  PLAYER-POSITION.
                   15  PLAYER-X           PIC S9(8).
                   15  PLAYER-Y           PIC S9(8).
                   15  PLAYER-Z           PIC S9(8).
               10  PLAYER-ANGLE           PIC S9(4).
               10  PLAYER-HEALTH          PIC 999.
                   88  PLAYER-DEAD        VALUE 000.
                   88  PLAYER-CRITICAL    VALUE 001 THRU 025.
                   88  PLAYER-HURT        VALUE 026 THRU 050.
                   88  PLAYER-HEALTHY     VALUE 051 THRU 100.
               10  PLAYER-ARMOR           PIC 999.
                   88  NO-ARMOR           VALUE 000.
                   88  LOW-ARMOR          VALUE 001 THRU 050.
                   88  GOOD-ARMOR         VALUE 051 THRU 200.
               10  PLAYER-STATUS          PIC X.
                   88  STATUS-ALIVE       VALUE 'A'.
                   88  STATUS-DEAD        VALUE 'D'.
                   88  STATUS-INVULN      VALUE 'I'.
               10  PLAYER-FLAGS           PIC X(8).
               10  FILLER                 PIC X(28).
           
           05  AMMUNITION-RECORD.
               10  AMMO-RECORD-TYPE       PIC X(8).
                   88  VALID-AMMO-REC     VALUE 'AMMO    '.
               10  AMMO-BULLETS           PIC 9(4).
                   88  NO-BULLETS         VALUE 0000.
                   88  LOW-BULLETS        VALUE 0001 THRU 0020.
               10  AMMO-SHELLS            PIC 9(4).
                   88  NO-SHELLS          VALUE 0000.
                   88  LOW-SHELLS         VALUE 0001 THRU 0010.
               10  AMMO-CELLS             PIC 9(4).
                   88  NO-CELLS           VALUE 0000.
                   88  LOW-CELLS          VALUE 0001 THRU 0040.
               10  AMMO-ROCKETS           PIC 9(4).
                   88  NO-ROCKETS         VALUE 0000.
                   88  LOW-ROCKETS        VALUE 0001 THRU 0005.
               10  CURRENT-WEAPON         PIC 9.
                   88  WEAPON-FIST        VALUE 0.
                   88  WEAPON-PISTOL      VALUE 1.
                   88  WEAPON-SHOTGUN     VALUE 2.
                   88  WEAPON-CHAINGUN    VALUE 3.
                   88  WEAPON-ROCKET      VALUE 4.
                   88  WEAPON-PLASMA      VALUE 5.
                   88  WEAPON-BFG         VALUE 6.
                   88  WEAPON-CHAINSAW    VALUE 7.
               10  FILLER                 PIC X(55).
       
       01  DOOM-ENTITY-TABLE.
           05  ENTITY-COUNT               PIC 99.
           05  ENTITY-ENTRY OCCURS 16 TIMES.
               10  ENTITY-RECORD-TYPE     PIC X(8).
                   88  VALID-ENTITY-REC   VALUE 'ENEMY   '.
               10  ENTITY-TYPE            PIC 99.
                   88  ENT-IMP            VALUE 01.
                   88  ENT-DEMON          VALUE 02.
                   88  ENT-BARON          VALUE 03.
                   88  ENT-ZOMBIE         VALUE 04.
                   88  ENT-SERGEANT       VALUE 05.
                   88  ENT-CACODEMON      VALUE 06.
                   88  ENT-LOST-SOUL      VALUE 07.
                   88  ENT-CYBERDEMON     VALUE 08.
                   88  ENT-SPIDER         VALUE 09.
               10  ENTITY-HEALTH          PIC 999.
               10  ENTITY-POSITION.
                   15  ENTITY-X           PIC S9(8).
                   15  ENTITY-Y           PIC S9(8).
               10  ENTITY-DISTANCE        PIC 9(5).
                   88  ENT-MELEE-RANGE    VALUE 00000 THRU 00064.
                   88  ENT-CLOSE-RANGE    VALUE 00065 THRU 00256.
                   88  ENT-MED-RANGE      VALUE 00257 THRU 00512.
                   88  ENT-LONG-RANGE     VALUE 00513 THRU 99999.
               10  ENTITY-ANGLE-TO        PIC S999.
               10  ENTITY-FLAGS           PIC X(8).
               10  FILLER                 PIC X(30).
       
       01  DOOM-COMMAND-RECORD.
           05  CMD-RECORD-TYPE            PIC X(8).
               88  VALID-CMD-REC          VALUE 'COMMAND '.
           05  CMD-ACTION                 PIC X(8).
               88  CMD-MOVE               VALUE 'MOVE    '.
               88  CMD-TURN               VALUE 'TURN    '.
               88  CMD-SHOOT              VALUE 'SHOOT   '.
               88  CMD-USE                VALUE 'USE     '.
               88  CMD-WEAPON             VALUE 'WEAPON  '.
               88  CMD-WAIT               VALUE 'WAIT    '.
           05  CMD-DIRECTION              PIC X(8).
               88  DIR-FORWARD            VALUE 'FORWARD '.
               88  DIR-BACK               VALUE 'BACK    '.
               88  DIR-LEFT               VALUE 'LEFT    '.
               88  DIR-RIGHT              VALUE 'RIGHT   '.
           05  CMD-VALUE                  PIC 9(4).
           05  CMD-PRIORITY               PIC 9.
               88  PRI-CRITICAL           VALUE 9.
               88  PRI-HIGH               VALUE 7 THRU 8.
               88  PRI-NORMAL             VALUE 4 THRU 6.
               88  PRI-LOW                VALUE 1 THRU 3.
           05  CMD-REASON                 PIC X(20).
           05  FILLER                     PIC X(31).
       
       01  DOOM-AI-WORKSPACE.
           05  AI-MODE                    PIC X.
               88  MODE-SURVIVAL          VALUE 'S'.
               88  MODE-COMBAT            VALUE 'C'.
               88  MODE-EXPLORE           VALUE 'E'.
               88  MODE-SCAVENGE          VALUE 'H'.
           05  AI-THREAT-LEVEL            PIC 9.
               88  NO-THREAT              VALUE 0.
               88  LOW-THREAT             VALUE 1 THRU 3.
               88  MED-THREAT             VALUE 4 THRU 6.
               88  HIGH-THREAT            VALUE 7 THRU 9.
           05  AI-DECISION-FACTORS.
               10  HEALTH-FACTOR          PIC S999.
               10  AMMO-FACTOR            PIC S999.
               10  ENEMY-FACTOR           PIC S999.
               10  DISTANCE-FACTOR        PIC S999.
           05  AI-TARGET.
               10  TARGET-INDEX           PIC 99.
               10  TARGET-PRIORITY        PIC 9.
           05  AI-PATH-PLAN.
               10  PLANNED-MOVES          PIC 99.
               10  MOVE-SEQUENCE OCCURS 10 TIMES.
                   15  MOVE-ACTION        PIC X(8).
                   15  MOVE-VALUE         PIC 9(4).