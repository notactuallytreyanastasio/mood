       IDENTIFICATION DIVISION.
       PROGRAM-ID. DOOMAI.
      *
      * DOOM AI MAIN CONTROL PROGRAM
      * This is the brain that decides DOOM tactics
      *
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT GAME-STATE ASSIGN TO GAMESTAT
               ORGANIZATION IS SEQUENTIAL.
           SELECT ENTITIES ASSIGN TO ENTITIES
               ORGANIZATION IS SEQUENTIAL.
           SELECT COMMANDS ASSIGN TO COMMANDS
               ORGANIZATION IS SEQUENTIAL.
           SELECT LOG-FILE ASSIGN TO LOGFILE
               ORGANIZATION IS SEQUENTIAL.
           
       DATA DIVISION.
       FILE SECTION.
       FD  GAME-STATE
           RECORDING MODE IS F
           RECORD CONTAINS 80 CHARACTERS.
       01  STATE-RECORD        PIC X(80).
           
       FD  ENTITIES
           RECORDING MODE IS F
           RECORD CONTAINS 120 CHARACTERS.
       01  ENTITY-RECORD       PIC X(120).
           
       FD  COMMANDS
           RECORDING MODE IS F
           RECORD CONTAINS 80 CHARACTERS.
       01  COMMAND-RECORD      PIC X(80).
           
       FD  LOG-FILE
           RECORDING MODE IS F
           RECORD CONTAINS 132 CHARACTERS.
       01  LOG-RECORD          PIC X(132).
           
       WORKING-STORAGE SECTION.
       01  WS-GAME-STATE.
           05  WS-TICK         PIC 9(9).
           05  WS-PLAYER-X     PIC S9(9).
           05  WS-PLAYER-Y     PIC S9(9).
           05  WS-PLAYER-Z     PIC S9(9).
           05  WS-PLAYER-ANGLE PIC S9(3).
           05  WS-HEALTH       PIC 9(3).
           05  WS-ARMOR        PIC 9(3).
           05  WS-AMMO         OCCURS 6 TIMES PIC 9(3).
           05  WS-WEAPON       PIC 9.
           05  WS-LEVEL        PIC 99.
           
       01  WS-AI-STATE.
           05  WS-MODE         PIC X(10).
           05  WS-TARGET-X     PIC S9(9).
           05  WS-TARGET-Y     PIC S9(9).
           05  WS-THREAT-LEVEL PIC 9.
           05  WS-LAST-HEALTH  PIC 9(3) VALUE 100.
           
       01  WS-DECISIONS.
           05  WS-ACTION       PIC X(10).
           05  WS-DIRECTION    PIC X(10).
           05  WS-AMOUNT       PIC 9(3).
           
       01  WS-CONSTANTS.
           05  C-LOW-HEALTH    PIC 9(3) VALUE 30.
           05  C-LOW-AMMO      PIC 9(3) VALUE 10.
           05  C-DANGER-DIST   PIC 9(5) VALUE 200.
           
       01  WS-WORK-AREAS.
           05  WS-DISTANCE     PIC 9(9).
           05  WS-ANGLE-DIFF   PIC S9(3).
           05  WS-COMMAND      PIC X(80).
           05  WS-LOG-MSG      PIC X(132).
           
       PROCEDURE DIVISION.
       MAIN-CONTROL.
           PERFORM INITIALIZATION
           PERFORM PROCESS-GAME-STATE
           PERFORM ANALYZE-SITUATION
           PERFORM MAKE-DECISION
           PERFORM EXECUTE-DECISION
           PERFORM CLEANUP
           STOP RUN.
           
       INITIALIZATION.
           OPEN INPUT GAME-STATE ENTITIES
           OPEN OUTPUT COMMANDS LOG-FILE
           MOVE 'DOOM AI INITIALIZED' TO WS-LOG-MSG
           WRITE LOG-RECORD FROM WS-LOG-MSG.
           
       PROCESS-GAME-STATE.
           READ GAME-STATE INTO STATE-RECORD
               AT END
                   MOVE 'NO GAME STATE' TO WS-LOG-MSG
                   WRITE LOG-RECORD FROM WS-LOG-MSG
                   MOVE 16 TO RETURN-CODE
                   STOP RUN.
                   
           PERFORM PARSE-GAME-STATE.
           
       PARSE-GAME-STATE.
      *    Extract fields from fixed-format record
           MOVE STATE-RECORD(1:9) TO WS-TICK
           MOVE STATE-RECORD(10:10) TO WS-PLAYER-X
           MOVE STATE-RECORD(20:10) TO WS-PLAYER-Y
           MOVE STATE-RECORD(30:10) TO WS-PLAYER-Z
           MOVE STATE-RECORD(40:4) TO WS-PLAYER-ANGLE
           MOVE STATE-RECORD(44:3) TO WS-HEALTH
           MOVE STATE-RECORD(47:3) TO WS-ARMOR
      *    Parse ammo counts
           MOVE STATE-RECORD(50:3) TO WS-AMMO(1)
           MOVE STATE-RECORD(53:3) TO WS-AMMO(2)
           MOVE STATE-RECORD(56:3) TO WS-AMMO(3)
           MOVE STATE-RECORD(59:3) TO WS-AMMO(4)
           MOVE STATE-RECORD(62:3) TO WS-AMMO(5)
           MOVE STATE-RECORD(65:3) TO WS-AMMO(6)
           MOVE STATE-RECORD(68:1) TO WS-WEAPON
           MOVE STATE-RECORD(69:2) TO WS-LEVEL.
           
       ANALYZE-SITUATION.
      *    Determine AI mode based on game state
           EVALUATE TRUE
               WHEN WS-HEALTH < C-LOW-HEALTH
                   MOVE 'SURVIVAL' TO WS-MODE
                   MOVE 9 TO WS-THREAT-LEVEL
                   
               WHEN WS-HEALTH < WS-LAST-HEALTH
                   MOVE 'COMBAT' TO WS-MODE
                   MOVE 7 TO WS-THREAT-LEVEL
                   
               WHEN WS-AMMO(WS-WEAPON) < C-LOW-AMMO
                   MOVE 'SCAVENGE' TO WS-MODE
                   MOVE 3 TO WS-THREAT-LEVEL
                   
               WHEN OTHER
                   MOVE 'EXPLORE' TO WS-MODE
                   MOVE 1 TO WS-THREAT-LEVEL
           END-EVALUATE.
           
           MOVE WS-HEALTH TO WS-LAST-HEALTH.
           
           STRING 'MODE: ' DELIMITED BY SIZE
                  WS-MODE DELIMITED BY SPACE
                  ' HEALTH: ' DELIMITED BY SIZE
                  WS-HEALTH DELIMITED BY SIZE
                  INTO WS-LOG-MSG
           WRITE LOG-RECORD FROM WS-LOG-MSG.
           
       MAKE-DECISION.
           EVALUATE WS-MODE
               WHEN 'SURVIVAL'
                   PERFORM DECIDE-SURVIVAL
               WHEN 'COMBAT'
                   PERFORM DECIDE-COMBAT
               WHEN 'SCAVENGE'
                   PERFORM DECIDE-SCAVENGE
               WHEN 'EXPLORE'
                   PERFORM DECIDE-EXPLORE
           END-EVALUATE.
           
       DECIDE-SURVIVAL.
      *    Low health - find cover and health items
           MOVE 'MOVE' TO WS-ACTION
           MOVE 'BACK' TO WS-DIRECTION
           MOVE 2 TO WS-AMOUNT
           MOVE 'RETREATING TO FIND HEALTH' TO WS-LOG-MSG
           WRITE LOG-RECORD FROM WS-LOG-MSG.
           
       DECIDE-COMBAT.
      *    Under attack - fight back
           MOVE 'TURN' TO WS-ACTION
           MOVE 'RIGHT' TO WS-DIRECTION
           MOVE 45 TO WS-AMOUNT
           MOVE 'COMBAT - SCANNING FOR ENEMIES' TO WS-LOG-MSG
           WRITE LOG-RECORD FROM WS-LOG-MSG.
           
           PERFORM WRITE-TURN-COMMAND
           
           MOVE 'SHOOT' TO WS-ACTION
           MOVE 3 TO WS-AMOUNT
           PERFORM WRITE-SHOOT-COMMAND.
           
       DECIDE-SCAVENGE.
      *    Low ammo - look for supplies
           MOVE 'MOVE' TO WS-ACTION
           MOVE 'FORWARD' TO WS-DIRECTION
           MOVE 1 TO WS-AMOUNT
           MOVE 'SEARCHING FOR AMMO' TO WS-LOG-MSG
           WRITE LOG-RECORD FROM WS-LOG-MSG.
           
       DECIDE-EXPLORE.
      *    Default - explore the level
           MOVE 'MOVE' TO WS-ACTION
           MOVE 'FORWARD' TO WS-DIRECTION
           MOVE 2 TO WS-AMOUNT
           MOVE 'EXPLORING LEVEL' TO WS-LOG-MSG
           WRITE LOG-RECORD FROM WS-LOG-MSG.
           
       EXECUTE-DECISION.
           EVALUATE WS-ACTION
               WHEN 'MOVE'
                   PERFORM WRITE-MOVE-COMMAND
               WHEN 'TURN'
                   PERFORM WRITE-TURN-COMMAND
               WHEN 'SHOOT'
                   PERFORM WRITE-SHOOT-COMMAND
               WHEN 'USE'
                   PERFORM WRITE-USE-COMMAND
           END-EVALUATE.
           
       WRITE-MOVE-COMMAND.
           STRING WS-ACTION DELIMITED BY SPACE
                  ' ' DELIMITED BY SIZE
                  WS-DIRECTION DELIMITED BY SPACE
                  ' ' DELIMITED BY SIZE
                  WS-AMOUNT DELIMITED BY SIZE
                  INTO WS-COMMAND
           WRITE COMMAND-RECORD FROM WS-COMMAND.
           
       WRITE-TURN-COMMAND.
           STRING 'TURN' DELIMITED BY SIZE
                  ' ' DELIMITED BY SIZE
                  WS-DIRECTION DELIMITED BY SPACE
                  ' ' DELIMITED BY SIZE
                  WS-AMOUNT DELIMITED BY SIZE
                  INTO WS-COMMAND
           WRITE COMMAND-RECORD FROM WS-COMMAND.
           
       WRITE-SHOOT-COMMAND.
           STRING 'SHOOT' DELIMITED BY SIZE
                  ' ' DELIMITED BY SIZE
                  WS-AMOUNT DELIMITED BY SIZE
                  INTO WS-COMMAND
           WRITE COMMAND-RECORD FROM WS-COMMAND.
           
       WRITE-USE-COMMAND.
           MOVE 'USE' TO WS-COMMAND
           WRITE COMMAND-RECORD FROM WS-COMMAND.
           
       CLEANUP.
           CLOSE GAME-STATE ENTITIES COMMANDS LOG-FILE
           MOVE 'AI CYCLE COMPLETE' TO WS-LOG-MSG
           WRITE LOG-RECORD FROM WS-LOG-MSG.