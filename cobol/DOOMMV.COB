       IDENTIFICATION DIVISION.
       PROGRAM-ID. DOOMMV.
      *
      * DOOM MOVEMENT PROCESSOR
      * Updates player position based on direction
      *
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT GAME-STATE ASSIGN TO 'GAMESTAT'.
           SELECT LEVEL-DATA ASSIGN TO 'LEVEL'.
           
       DATA DIVISION.
       FILE SECTION.
       FD  GAME-STATE.
       01  GAME-STATE-REC.
           05  PLAYER-X        PIC 99.
           05  PLAYER-Y        PIC 99.
           05  PLAYER-HEALTH   PIC 999.
           05  PLAYER-AMMO     PIC 999.
           05  PLAYER-FACING   PIC X.
           05  FILLER          PIC X(68).
           
       FD  LEVEL-DATA.
       01  LEVEL-REC         PIC X(80).
       
       WORKING-STORAGE SECTION.
       01  WS-MAP-ARRAY.
           05  WS-MAP-ROW OCCURS 20 TIMES.
               10  WS-MAP-CELL OCCURS 40 TIMES PIC X.
               
       01  WS-INDICES.
           05  WS-I            PIC 99.
           05  WS-NEW-X        PIC 99.
           05  WS-NEW-Y        PIC 99.
           
       01  WS-TARGET-CELL      PIC X.
       01  WS-RETURN-CODE      PIC 99 VALUE ZERO.
       
       LINKAGE SECTION.
       01  PARM-DATA.
           05  PARM-LEN        PIC S9(4) COMP.
           05  PARM-DIRECTION  PIC X.
           
       PROCEDURE DIVISION USING PARM-DATA.
       MAIN-LOGIC.
           OPEN I-O GAME-STATE
           OPEN INPUT LEVEL-DATA
           
           READ GAME-STATE
           
           PERFORM LOAD-MAP
           PERFORM CALCULATE-NEW-POSITION
           PERFORM CHECK-COLLISION
           
           IF WS-RETURN-CODE = ZERO
               PERFORM UPDATE-POSITION
               REWRITE GAME-STATE-REC
           END-IF
           
           CLOSE GAME-STATE LEVEL-DATA
           
           MOVE WS-RETURN-CODE TO RETURN-CODE
           STOP RUN.
           
       LOAD-MAP.
           PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > 20
               READ LEVEL-DATA
               MOVE LEVEL-REC TO WS-MAP-ROW(WS-I)
           END-PERFORM.
           
       CALCULATE-NEW-POSITION.
           MOVE PLAYER-X TO WS-NEW-X
           MOVE PLAYER-Y TO WS-NEW-Y
           
           EVALUATE PARM-DIRECTION
               WHEN 'N'
                   SUBTRACT 1 FROM WS-NEW-Y
                   MOVE 'N' TO PLAYER-FACING
               WHEN 'S'
                   ADD 1 TO WS-NEW-Y
                   MOVE 'S' TO PLAYER-FACING
               WHEN 'E'
                   ADD 1 TO WS-NEW-X
                   MOVE 'E' TO PLAYER-FACING
               WHEN 'W'
                   SUBTRACT 1 FROM WS-NEW-X
                   MOVE 'W' TO PLAYER-FACING
           END-EVALUATE.
           
       CHECK-COLLISION.
           IF WS-NEW-X < 1 OR WS-NEW-X > 40 OR
              WS-NEW-Y < 1 OR WS-NEW-Y > 20
               MOVE 4 TO WS-RETURN-CODE
           ELSE
               MOVE WS-MAP-CELL(WS-NEW-Y, WS-NEW-X) TO WS-TARGET-CELL
               
               EVALUATE WS-TARGET-CELL
                   WHEN '#'
                       MOVE 4 TO WS-RETURN-CODE
                   WHEN 'D'
                       MOVE 8 TO WS-RETURN-CODE
                   WHEN '$'
                       ADD 50 TO PLAYER-AMMO
                       MOVE '.' TO WS-MAP-CELL(WS-NEW-Y, WS-NEW-X)
               END-EVALUATE
           END-IF.
           
       UPDATE-POSITION.
           MOVE WS-NEW-X TO PLAYER-X
           MOVE WS-NEW-Y TO PLAYER-Y.