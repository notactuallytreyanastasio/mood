      *================================================================
      * DOOMAI2.COB - Enhanced DOOM AI with Complete State Processing
      * Reads mapped COBOL structures and makes tactical decisions
      *================================================================
       IDENTIFICATION DIVISION.
       PROGRAM-ID. DOOMAI2.
       AUTHOR. DOOM-COBOL-SYSTEM.
       
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT GAMESTAT-FILE ASSIGN TO 'DOOM.GAMESTAT'
               ORGANIZATION IS SEQUENTIAL.
           
           SELECT COMMANDS-FILE ASSIGN TO 'DOOM.COMMANDS'
               ORGANIZATION IS SEQUENTIAL.
           
           SELECT LOG-FILE ASSIGN TO 'DOOM.AILOG'
               ORGANIZATION IS SEQUENTIAL.
       
       DATA DIVISION.
       FILE SECTION.
       FD  GAMESTAT-FILE.
       01  GAMESTAT-RECORD                PIC X(80).
       
       FD  COMMANDS-FILE.
       01  COMMANDS-RECORD                PIC X(80).
       
       FD  LOG-FILE.
       01  LOG-RECORD                     PIC X(80).
       
       WORKING-STORAGE SECTION.
       COPY DOOMSTAT.
       
       01  WS-FILE-STATUS                 PIC XX.
           88  EOF-REACHED                VALUE '10'.
       
       01  WS-COUNTERS.
           05  WS-ENEMY-COUNT             PIC 99 VALUE ZERO.
           05  WS-COMMAND-COUNT           PIC 99 VALUE ZERO.
           05  WS-CLOSEST-ENEMY           PIC 99 VALUE ZERO.
           05  WS-TOTAL-THREAT            PIC 999 VALUE ZERO.
       
       01  WS-DECISIONS.
           05  WS-PRIMARY-ACTION          PIC X(8).
           05  WS-SECONDARY-ACTION        PIC X(8).
           05  WS-ACTION-VALUE            PIC 9999.
           05  WS-ACTION-REASON           PIC X(30).
       
       01  WS-THREAT-ANALYSIS.
           05  WS-CLOSEST-DISTANCE        PIC 9(5) VALUE 99999.
           05  WS-ENEMY-DPS               PIC 999 VALUE ZERO.
           05  WS-TIME-TO-KILL            PIC 999 VALUE ZERO.
           05  WS-ESCAPE-DIRECTION        PIC X(8).
       
       01  WS-MOVEMENT-PLAN.
           05  WS-SAFE-X                  PIC S9(8).
           05  WS-SAFE-Y                  PIC S9(8).
           05  WS-MOVE-PRIORITY           PIC 9.
       
       PROCEDURE DIVISION.
       MAIN-PROCEDURE.
           PERFORM INITIALIZATION
           PERFORM READ-GAME-STATE
           PERFORM ANALYZE-SITUATION
           PERFORM MAKE-DECISION
           PERFORM WRITE-COMMANDS
           PERFORM CLEANUP
           GOBACK.
       
       INITIALIZATION.
           OPEN INPUT GAMESTAT-FILE
           OPEN OUTPUT COMMANDS-FILE
           OPEN OUTPUT LOG-FILE
           
           INITIALIZE DOOM-AI-WORKSPACE
           MOVE ZERO TO WS-ENEMY-COUNT
           MOVE ZERO TO WS-COMMAND-COUNT.
       
       READ-GAME-STATE.
           PERFORM READ-STATE-HEADER
           PERFORM READ-PLAYER-DATA
           PERFORM READ-AMMO-DATA
           PERFORM READ-ENEMY-DATA UNTIL EOF-REACHED.
       
       READ-STATE-HEADER.
           READ GAMESTAT-FILE INTO STATE-HEADER
               AT END SET EOF-REACHED TO TRUE
           END-READ
           
           IF VALID-STATE-REC
               MOVE STATE-TICK TO LOG-RECORD
               WRITE LOG-RECORD
           END-IF.
       
       READ-PLAYER-DATA.
           READ GAMESTAT-FILE INTO PLAYER-RECORD
               AT END SET EOF-REACHED TO TRUE
           END-READ
           
           IF VALID-PLAYER-REC
               PERFORM EVALUATE-HEALTH-STATUS
           END-IF.
       
       READ-AMMO-DATA.
           READ GAMESTAT-FILE INTO AMMUNITION-RECORD
               AT END SET EOF-REACHED TO TRUE
           END-READ
           
           IF VALID-AMMO-REC
               PERFORM EVALUATE-AMMO-STATUS
           END-IF.
       
       READ-ENEMY-DATA.
           READ GAMESTAT-FILE AT END SET EOF-REACHED TO TRUE
           END-READ
           
           IF NOT EOF-REACHED
               MOVE GAMESTAT-RECORD TO ENTITY-ENTRY(WS-ENEMY-COUNT + 1)
               
               IF VALID-ENTITY-REC
                   ADD 1 TO WS-ENEMY-COUNT
                   PERFORM ANALYZE-ENEMY
               END-IF
           END-IF.
       
       EVALUATE-HEALTH-STATUS.
           EVALUATE TRUE
               WHEN PLAYER-DEAD
                   MOVE 'S' TO AI-MODE
                   MOVE 9 TO AI-THREAT-LEVEL
                   
               WHEN PLAYER-CRITICAL
                   MOVE 'S' TO AI-MODE
                   MOVE 8 TO AI-THREAT-LEVEL
                   MOVE -900 TO HEALTH-FACTOR
                   
               WHEN PLAYER-HURT
                   MOVE 'C' TO AI-MODE
                   MOVE 5 TO AI-THREAT-LEVEL
                   MOVE -300 TO HEALTH-FACTOR
                   
               WHEN PLAYER-HEALTHY
                   MOVE 'E' TO AI-MODE
                   MOVE 2 TO AI-THREAT-LEVEL
                   MOVE 100 TO HEALTH-FACTOR
           END-EVALUATE.
       
       EVALUATE-AMMO-STATUS.
           MOVE ZERO TO AMMO-FACTOR
           
           EVALUATE TRUE
               WHEN WEAPON-SHOTGUN
                   IF NO-SHELLS
                       SUBTRACT 500 FROM AMMO-FACTOR
                   ELSE IF LOW-SHELLS
                       SUBTRACT 200 FROM AMMO-FACTOR
                   END-IF
                   
               WHEN WEAPON-CHAINGUN
                   IF NO-BULLETS
                       SUBTRACT 500 FROM AMMO-FACTOR
                   ELSE IF LOW-BULLETS
                       SUBTRACT 300 FROM AMMO-FACTOR
                   END-IF
                   
               WHEN WEAPON-ROCKET
                   IF NO-ROCKETS
                       SUBTRACT 800 FROM AMMO-FACTOR
                   ELSE IF LOW-ROCKETS
                       SUBTRACT 400 FROM AMMO-FACTOR
                   END-IF
           END-EVALUATE.
       
       ANALYZE-ENEMY.
           IF ENTITY-DISTANCE(WS-ENEMY-COUNT) < WS-CLOSEST-DISTANCE
               MOVE ENTITY-DISTANCE(WS-ENEMY-COUNT) 
                    TO WS-CLOSEST-DISTANCE
               MOVE WS-ENEMY-COUNT TO WS-CLOSEST-ENEMY
           END-IF
           
           EVALUATE TRUE
               WHEN ENT-IMP
                   ADD 30 TO WS-TOTAL-THREAT
                   
               WHEN ENT-DEMON
                   ADD 50 TO WS-TOTAL-THREAT
                   
               WHEN ENT-BARON
                   ADD 80 TO WS-TOTAL-THREAT
                   
               WHEN ENT-CYBERDEMON
                   ADD 150 TO WS-TOTAL-THREAT
                   
               WHEN OTHER
                   ADD 40 TO WS-TOTAL-THREAT
           END-EVALUATE.
       
       ANALYZE-SITUATION.
           MOVE WS-TOTAL-THREAT TO ENEMY-FACTOR
           
           IF WS-CLOSEST-DISTANCE < 256
               ADD 500 TO ENEMY-FACTOR
               MOVE 7 TO AI-THREAT-LEVEL
           ELSE IF WS-CLOSEST-DISTANCE < 512
               ADD 200 TO ENEMY-FACTOR
               MOVE 5 TO AI-THREAT-LEVEL
           END-IF
           
           COMPUTE DISTANCE-FACTOR = 1000 - WS-CLOSEST-DISTANCE
           
           IF MODE-SURVIVAL
               PERFORM PLAN-RETREAT
           ELSE IF MODE-COMBAT AND WS-ENEMY-COUNT > 0
               PERFORM PLAN-COMBAT
           ELSE
               PERFORM PLAN-EXPLORATION
           END-IF.
       
       PLAN-RETREAT.
           MOVE "SURVIVAL RETREAT" TO WS-ACTION-REASON
           
           IF WS-CLOSEST-ENEMY > 0
               IF ENTITY-X(WS-CLOSEST-ENEMY) > PLAYER-X
                   MOVE 'LEFT' TO WS-ESCAPE-DIRECTION
               ELSE
                   MOVE 'RIGHT' TO WS-ESCAPE-DIRECTION
               END-IF
               
               MOVE 'MOVE' TO WS-PRIMARY-ACTION
               MOVE 'BACK' TO CMD-DIRECTION
               MOVE 0020 TO WS-ACTION-VALUE
               
               MOVE 'TURN' TO WS-SECONDARY-ACTION
           ELSE
               MOVE 'MOVE' TO WS-PRIMARY-ACTION
               MOVE 'BACK' TO CMD-DIRECTION
               MOVE 0030 TO WS-ACTION-VALUE
           END-IF.
       
       PLAN-COMBAT.
           MOVE "COMBAT ENGAGEMENT" TO WS-ACTION-REASON
           
           IF WS-CLOSEST-ENEMY > 0
               IF ENT-MELEE-RANGE
                   MOVE 'MOVE' TO WS-PRIMARY-ACTION
                   MOVE 'BACK' TO CMD-DIRECTION
                   MOVE 0010 TO WS-ACTION-VALUE
                   
               ELSE IF ENT-CLOSE-RANGE
                   MOVE 'SHOOT' TO WS-PRIMARY-ACTION
                   MOVE 0003 TO WS-ACTION-VALUE
                   
                   MOVE 'MOVE' TO WS-SECONDARY-ACTION
                   MOVE 'LEFT' TO CMD-DIRECTION
                   
               ELSE
                   MOVE 'MOVE' TO WS-PRIMARY-ACTION
                   MOVE 'FORWARD' TO CMD-DIRECTION
                   MOVE 0010 TO WS-ACTION-VALUE
                   
                   MOVE 'SHOOT' TO WS-SECONDARY-ACTION
               END-IF
           END-IF.
       
       PLAN-EXPLORATION.
           MOVE "EXPLORATION MODE" TO WS-ACTION-REASON
           
           MOVE 'MOVE' TO WS-PRIMARY-ACTION
           MOVE 'FORWARD' TO CMD-DIRECTION
           MOVE 0020 TO WS-ACTION-VALUE
           
           MOVE 'TURN' TO WS-SECONDARY-ACTION
           MOVE 'RIGHT' TO CMD-DIRECTION.
       
       MAKE-DECISION.
           IF WS-PRIMARY-ACTION NOT = SPACES
               PERFORM WRITE-PRIMARY-COMMAND
           END-IF
           
           IF WS-SECONDARY-ACTION NOT = SPACES
               PERFORM WRITE-SECONDARY-COMMAND
           END-IF
           
           IF WS-COMMAND-COUNT = ZERO
               PERFORM WRITE-DEFAULT-COMMAND
           END-IF.
       
       WRITE-PRIMARY-COMMAND.
           INITIALIZE DOOM-COMMAND-RECORD
           MOVE 'COMMAND ' TO CMD-RECORD-TYPE
           MOVE WS-PRIMARY-ACTION TO CMD-ACTION
           MOVE CMD-DIRECTION TO CMD-DIRECTION OF DOOM-COMMAND-RECORD
           MOVE WS-ACTION-VALUE TO CMD-VALUE
           
           IF MODE-SURVIVAL
               MOVE 9 TO CMD-PRIORITY
           ELSE IF MODE-COMBAT
               MOVE 7 TO CMD-PRIORITY
           ELSE
               MOVE 5 TO CMD-PRIORITY
           END-IF
           
           MOVE WS-ACTION-REASON TO CMD-REASON
           
           WRITE COMMANDS-RECORD FROM DOOM-COMMAND-RECORD
           ADD 1 TO WS-COMMAND-COUNT.
       
       WRITE-SECONDARY-COMMAND.
           INITIALIZE DOOM-COMMAND-RECORD
           MOVE 'COMMAND ' TO CMD-RECORD-TYPE
           MOVE WS-SECONDARY-ACTION TO CMD-ACTION
           
           IF WS-SECONDARY-ACTION = 'TURN'
               MOVE 'RIGHT' TO CMD-DIRECTION OF DOOM-COMMAND-RECORD
               MOVE 0030 TO CMD-VALUE
           ELSE IF WS-SECONDARY-ACTION = 'SHOOT'
               MOVE 0001 TO CMD-VALUE
           ELSE
               MOVE 0005 TO CMD-VALUE
           END-IF
           
           MOVE 3 TO CMD-PRIORITY
           MOVE "SECONDARY ACTION" TO CMD-REASON
           
           WRITE COMMANDS-RECORD FROM DOOM-COMMAND-RECORD
           ADD 1 TO WS-COMMAND-COUNT.
       
       WRITE-DEFAULT-COMMAND.
           INITIALIZE DOOM-COMMAND-RECORD
           MOVE 'COMMAND ' TO CMD-RECORD-TYPE
           MOVE 'WAIT' TO CMD-ACTION
           MOVE 0010 TO CMD-VALUE
           MOVE 1 TO CMD-PRIORITY
           MOVE "NO ACTION DETERMINED" TO CMD-REASON
           
           WRITE COMMANDS-RECORD FROM DOOM-COMMAND-RECORD.
       
       CLEANUP.
           MOVE "AI COMPLETE - COMMANDS: " TO LOG-RECORD
           MOVE WS-COMMAND-COUNT TO LOG-RECORD(25:2)
           WRITE LOG-RECORD
           
           CLOSE GAMESTAT-FILE
           CLOSE COMMANDS-FILE
           CLOSE LOG-FILE.