       IDENTIFICATION DIVISION.
       PROGRAM-ID. DOOMTACT.
      *
      * DOOM TACTICAL DECISION ENGINE
      * Analyzes game state and makes combat decisions
      *
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT GAME-STATE ASSIGN TO 'GAMESTAT'
               ORGANIZATION IS SEQUENTIAL.
           SELECT ENTITIES ASSIGN TO 'ENTITIES'
               ORGANIZATION IS SEQUENTIAL.
           SELECT TACTICS ASSIGN TO 'TACTICS'
               ORGANIZATION IS SEQUENTIAL.
           SELECT COMMANDS ASSIGN TO 'COMMANDS'
               ORGANIZATION IS SEQUENTIAL.
           
       DATA DIVISION.
       FILE SECTION.
       FD  GAME-STATE
           RECORDING MODE IS F
           RECORD CONTAINS 80 CHARACTERS.
       01  STATE-RECORD.
           05  GAME-TICK           PIC 9(9).
           05  PLAYER-X            PIC S9(9) SIGN LEADING SEPARATE.
           05  PLAYER-Y            PIC S9(9) SIGN LEADING SEPARATE.
           05  PLAYER-Z            PIC S9(9) SIGN LEADING SEPARATE.
           05  PLAYER-ANGLE        PIC S9(3) SIGN LEADING SEPARATE.
           05  PLAYER-HEALTH       PIC 9(3).
           05  PLAYER-ARMOR        PIC 9(3).
           05  PLAYER-AMMO         OCCURS 6 TIMES PIC 9(3).
           05  CURRENT-WEAPON      PIC 9.
           05  CURRENT-LEVEL       PIC 99.
           
       FD  ENTITIES
           RECORDING MODE IS F
           RECORD CONTAINS 120 CHARACTERS.
       01  ENTITY-RECORD.
           05  ENTITY-TYPE         PIC X.
           05  ENTITY-SUBTYPE      PIC 99.
           05  ENTITY-X            PIC S9(9) SIGN LEADING SEPARATE.
           05  ENTITY-Y            PIC S9(9) SIGN LEADING SEPARATE.
           05  ENTITY-Z            PIC S9(9) SIGN LEADING SEPARATE.
           05  ENTITY-DISTANCE     PIC 9(5).
           05  ENTITY-ANGLE        PIC S9(3) SIGN LEADING SEPARATE.
           05  ENTITY-HEALTH       PIC 9(3).
           05  ENTITY-STATE        PIC X.
           05  FILLER              PIC X(66).
           
       FD  TACTICS
           RECORDING MODE IS F
           RECORD CONTAINS 100 CHARACTERS.
       01  TACTICS-RECORD.
           05  THREAT-LEVEL        PIC 9.
           05  PRIMARY-TARGET.
               10  TARGET-TYPE     PIC X.
               10  TARGET-X        PIC S9(9) SIGN LEADING SEPARATE.
               10  TARGET-Y        PIC S9(9) SIGN LEADING SEPARATE.
               10  TARGET-ANGLE    PIC S9(3) SIGN LEADING SEPARATE.
           05  MOVE-DIRECTION      PIC X.
           05  MOVE-URGENCY        PIC 9.
           05  ACTION-COUNT        PIC 9.
           05  ACTION-QUEUE        OCCURS 5 TIMES.
               10  ACTION-CODE     PIC XX.
               10  ACTION-PARAM    PIC S9(3) SIGN LEADING SEPARATE.
           05  FILLER              PIC X(35).
           
       FD  COMMANDS
           RECORDING MODE IS F
           RECORD CONTAINS 80 CHARACTERS.
       01  COMMAND-RECORD.
           05  COMMAND-TYPE        PIC X.
           05  COMMAND-ACTION      PIC X.
           05  COMMAND-CODE        PIC X(4).
           05  MOUSE-DELTA-X       PIC S9(3) SIGN LEADING SEPARATE.
           05  MOUSE-DELTA-Y       PIC S9(3) SIGN LEADING SEPARATE.
           05  FILLER              PIC X(66).
           
       WORKING-STORAGE SECTION.
       01  WS-CONSTANTS.
           05  PI                  PIC 9V9(8) VALUE 3.14159265.
           05  DANGER-DISTANCE     PIC 9(5) VALUE 200.
           05  CRITICAL-HEALTH     PIC 999 VALUE 030.
           05  LOW-AMMO           PIC 999 VALUE 010.
           
       01  WS-THREAT-ANALYSIS.
           05  MONSTER-COUNT       PIC 99 VALUE ZERO.
           05  CLOSEST-MONSTER     PIC 99 VALUE ZERO.
           05  MIN-DISTANCE        PIC 9(5) VALUE 99999.
           05  TOTAL-THREAT        PIC 999 VALUE ZERO.
           05  THREAT-DIRECTION    PIC S9(3) VALUE ZERO.
           
       01  WS-CALCULATIONS.
           05  DELTA-X             PIC S9(9).
           05  DELTA-Y             PIC S9(9).
           05  ANGLE-TO-TARGET     PIC S9(3).
           05  ANGLE-DIFFERENCE    PIC S9(3).
           05  AIM-ADJUSTMENT-X    PIC S9(3).
           05  AIM-ADJUSTMENT-Y    PIC S9(3).
           
       01  WS-DECISION-FLAGS.
           05  NEED-HEALTH         PIC X VALUE 'N'.
           05  NEED-AMMO          PIC X VALUE 'N'.
           05  CAN-FIGHT          PIC X VALUE 'Y'.
           05  SHOULD-RETREAT     PIC X VALUE 'N'.
           
       01  WS-ENTITY-TABLE.
           05  WS-ENTITY OCCURS 50 TIMES.
               10  WS-ENT-TYPE     PIC X.
               10  WS-ENT-SUBTYPE  PIC 99.
               10  WS-ENT-X        PIC S9(9).
               10  WS-ENT-Y        PIC S9(9).
               10  WS-ENT-DISTANCE PIC 9(5).
               10  WS-ENT-ANGLE    PIC S9(3).
               10  WS-ENT-HEALTH   PIC 9(3).
               10  WS-ENT-STATE    PIC X.
               
       01  WS-SUBSCRIPTS.
           05  WS-I                PIC 99.
           05  WS-J                PIC 99.
           05  ENTITY-COUNT        PIC 99 VALUE ZERO.
           05  COMMAND-COUNT       PIC 99 VALUE ZERO.
           
       01  WS-RETURN-CODE         PIC 99 VALUE ZERO.
           
       PROCEDURE DIVISION.
       MAIN-LOGIC.
           OPEN INPUT GAME-STATE ENTITIES
           OPEN OUTPUT TACTICS COMMANDS
           
           PERFORM READ-GAME-STATE
           PERFORM READ-ALL-ENTITIES
           PERFORM ANALYZE-THREATS
           PERFORM MAKE-DECISION
           PERFORM GENERATE-COMMANDS
           
           CLOSE GAME-STATE ENTITIES TACTICS COMMANDS
           
           MOVE WS-RETURN-CODE TO RETURN-CODE
           STOP RUN.
           
       READ-GAME-STATE.
           READ GAME-STATE
               AT END
                   DISPLAY 'ERROR: No game state available'
                   MOVE 99 TO WS-RETURN-CODE
                   STOP RUN.
                   
       READ-ALL-ENTITIES.
           PERFORM UNTIL ENTITY-COUNT >= 50
               READ ENTITIES
                   AT END
                       EXIT PERFORM
                   NOT AT END
                       ADD 1 TO ENTITY-COUNT
                       MOVE ENTITY-TYPE TO WS-ENT-TYPE(ENTITY-COUNT)
                       MOVE ENTITY-SUBTYPE TO 
                            WS-ENT-SUBTYPE(ENTITY-COUNT)
                       MOVE ENTITY-X TO WS-ENT-X(ENTITY-COUNT)
                       MOVE ENTITY-Y TO WS-ENT-Y(ENTITY-COUNT)
                       MOVE ENTITY-DISTANCE TO 
                            WS-ENT-DISTANCE(ENTITY-COUNT)
                       MOVE ENTITY-ANGLE TO WS-ENT-ANGLE(ENTITY-COUNT)
                       MOVE ENTITY-HEALTH TO WS-ENT-HEALTH(ENTITY-COUNT)
                       MOVE ENTITY-STATE TO WS-ENT-STATE(ENTITY-COUNT)
               END-READ
           END-PERFORM.
           
       ANALYZE-THREATS.
           PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > ENTITY-COUNT
               IF WS-ENT-TYPE(WS-I) = 'M' AND WS-ENT-STATE(WS-I) = 'A'
                   ADD 1 TO MONSTER-COUNT
                   
      *            Calculate threat score based on distance and type
                   EVALUATE WS-ENT-SUBTYPE(WS-I)
                       WHEN 01 THRU 02  *> Zombieman/Shotgunner
                           COMPUTE TOTAL-THREAT = TOTAL-THREAT + 
                               (1000 / (WS-ENT-DISTANCE(WS-I) + 1))
                       WHEN 03 THRU 04  *> Imp/Demon  
                           COMPUTE TOTAL-THREAT = TOTAL-THREAT + 
                               (2000 / (WS-ENT-DISTANCE(WS-I) + 1))
                       WHEN OTHER       *> Bigger threats
                           COMPUTE TOTAL-THREAT = TOTAL-THREAT + 
                               (3000 / (WS-ENT-DISTANCE(WS-I) + 1))
                   END-EVALUATE
                   
      *            Track closest monster
                   IF WS-ENT-DISTANCE(WS-I) < MIN-DISTANCE
                       MOVE WS-ENT-DISTANCE(WS-I) TO MIN-DISTANCE
                       MOVE WS-I TO CLOSEST-MONSTER
                   END-IF
               END-IF
           END-PERFORM.
           
      *    Determine threat level
           EVALUATE TRUE
               WHEN TOTAL-THREAT > 100
                   MOVE 9 TO THREAT-LEVEL
               WHEN TOTAL-THREAT > 50
                   MOVE 7 TO THREAT-LEVEL
               WHEN TOTAL-THREAT > 20
                   MOVE 5 TO THREAT-LEVEL
               WHEN TOTAL-THREAT > 0
                   MOVE 3 TO THREAT-LEVEL
               WHEN OTHER
                   MOVE 0 TO THREAT-LEVEL
           END-EVALUATE.
           
       MAKE-DECISION.
      *    Check resource status
           IF PLAYER-HEALTH < CRITICAL-HEALTH
               MOVE 'Y' TO NEED-HEALTH
               MOVE 'N' TO CAN-FIGHT.
               
           IF PLAYER-AMMO(CURRENT-WEAPON) < LOW-AMMO
               MOVE 'Y' TO NEED-AMMO.
               
      *    Decide action based on situation
           EVALUATE TRUE
               WHEN NEED-HEALTH = 'Y' AND MIN-DISTANCE < DANGER-DISTANCE
                   MOVE 'Y' TO SHOULD-RETREAT
                   MOVE 20 TO WS-RETURN-CODE
                   
               WHEN MONSTER-COUNT > 0 AND CAN-FIGHT = 'Y'
                   PERFORM SETUP-COMBAT
                   MOVE 10 TO WS-RETURN-CODE
                   
               WHEN NEED-HEALTH = 'Y' OR NEED-AMMO = 'Y'
                   PERFORM FIND-ITEMS
                   MOVE 5 TO WS-RETURN-CODE
                   
               WHEN OTHER
                   PERFORM EXPLORE
                   MOVE 0 TO WS-RETURN-CODE
           END-EVALUATE.
           
       SETUP-COMBAT.
      *    Target closest active monster
           IF CLOSEST-MONSTER > 0
               MOVE 'M' TO TARGET-TYPE
               MOVE WS-ENT-X(CLOSEST-MONSTER) TO TARGET-X
               MOVE WS-ENT-Y(CLOSEST-MONSTER) TO TARGET-Y
               MOVE WS-ENT-ANGLE(CLOSEST-MONSTER) TO TARGET-ANGLE
               
      *        Calculate aim adjustment
               COMPUTE ANGLE-DIFFERENCE = 
                   WS-ENT-ANGLE(CLOSEST-MONSTER) - PLAYER-ANGLE
                   
      *        Normalize angle to -180 to 180
               IF ANGLE-DIFFERENCE > 180
                   SUBTRACT 360 FROM ANGLE-DIFFERENCE
               ELSE IF ANGLE-DIFFERENCE < -180
                   ADD 360 TO ANGLE-DIFFERENCE
               END-IF
               
      *        Convert angle to mouse movement
               COMPUTE AIM-ADJUSTMENT-X = ANGLE-DIFFERENCE * 5
               
      *        Add to action queue
               MOVE 1 TO ACTION-COUNT
               MOVE 'AIM' TO ACTION-CODE(1)
               MOVE AIM-ADJUSTMENT-X TO ACTION-PARAM(1)
               
               IF ABS(ANGLE-DIFFERENCE) < 5
      *            We're aimed, shoot!
                   ADD 1 TO ACTION-COUNT
                   MOVE 'FR' TO ACTION-CODE(2)
                   MOVE 0 TO ACTION-PARAM(2)
               END-IF
           END-IF.
           
       FIND-ITEMS.
      *    Look for health or ammo items
           PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > ENTITY-COUNT
               IF WS-ENT-TYPE(WS-I) = 'I'
                   EVALUATE WS-ENT-SUBTYPE(WS-I)
                       WHEN 10 THRU 19  *> Health items
                           IF NEED-HEALTH = 'Y'
                               MOVE 'I' TO TARGET-TYPE
                               MOVE WS-ENT-X(WS-I) TO TARGET-X
                               MOVE WS-ENT-Y(WS-I) TO TARGET-Y
                               MOVE 'E' TO MOVE-DIRECTION
                               MOVE 8 TO MOVE-URGENCY
                               EXIT PERFORM
                           END-IF
                       WHEN 20 THRU 29  *> Ammo items
                           IF NEED-AMMO = 'Y'
                               MOVE 'I' TO TARGET-TYPE
                               MOVE WS-ENT-X(WS-I) TO TARGET-X
                               MOVE WS-ENT-Y(WS-I) TO TARGET-Y
                               MOVE 'E' TO MOVE-DIRECTION
                               MOVE 6 TO MOVE-URGENCY
                               EXIT PERFORM
                           END-IF
                   END-EVALUATE
               END-IF
           END-PERFORM.
           
       EXPLORE.
      *    Basic exploration - move forward
           MOVE 'X' TO TARGET-TYPE
           MOVE 0 TO TARGET-X TARGET-Y TARGET-ANGLE
           MOVE 'N' TO MOVE-DIRECTION
           MOVE 3 TO MOVE-URGENCY
           MOVE 1 TO ACTION-COUNT
           MOVE 'MV' TO ACTION-CODE(1)
           MOVE 0 TO ACTION-PARAM(1).
           
       GENERATE-COMMANDS.
      *    Write tactical analysis
           WRITE TACTICS-RECORD
           
      *    Generate keyboard/mouse commands
           PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > ACTION-COUNT
               EVALUATE ACTION-CODE(WS-I)
                   WHEN 'AIM'
                       MOVE 'M' TO COMMAND-TYPE
                       MOVE 'P' TO COMMAND-ACTION
                       MOVE 'MOVE' TO COMMAND-CODE
                       MOVE ACTION-PARAM(WS-I) TO MOUSE-DELTA-X
                       MOVE 0 TO MOUSE-DELTA-Y
                       WRITE COMMAND-RECORD
                       
                   WHEN 'FR'
                       MOVE 'M' TO COMMAND-TYPE
                       MOVE 'P' TO COMMAND-ACTION
                       MOVE 'BTN1' TO COMMAND-CODE
                       MOVE 0 TO MOUSE-DELTA-X MOUSE-DELTA-Y
                       WRITE COMMAND-RECORD
                       
                   WHEN 'MV'
                       MOVE 'K' TO COMMAND-TYPE
                       MOVE 'P' TO COMMAND-ACTION
                       MOVE 'W   ' TO COMMAND-CODE
                       MOVE 0 TO MOUSE-DELTA-X MOUSE-DELTA-Y
                       WRITE COMMAND-RECORD
               END-EVALUATE
           END-PERFORM.