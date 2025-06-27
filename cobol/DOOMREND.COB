       IDENTIFICATION DIVISION.
       PROGRAM-ID. DOOMREND.
      *
      * DOOM ASCII RENDERER
      * Renders the game view based on current state
      *
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT GAME-STATE ASSIGN TO 'GAMESTAT'.
           SELECT LEVEL-DATA ASSIGN TO 'LEVEL'.
           SELECT DISPLAY-FILE ASSIGN TO 'DISPLAY'.
           
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
       
       FD  DISPLAY-FILE.
       01  DISPLAY-LINE      PIC X(133).
       
       WORKING-STORAGE SECTION.
       01  WS-MAP-ARRAY.
           05  WS-MAP-ROW OCCURS 20 TIMES.
               10  WS-MAP-CELL OCCURS 40 TIMES PIC X.
               
       01  WS-VIEWPORT.
           05  WS-VIEW-ROW OCCURS 10 TIMES.
               10  WS-VIEW-CELL OCCURS 20 TIMES PIC X.
               
       01  WS-INDICES.
           05  WS-I          PIC 99.
           05  WS-J          PIC 99.
           05  WS-VIEW-X     PIC 99.
           05  WS-VIEW-Y     PIC 99.
           
       01  WS-DISPLAY-LINE.
           05  FILLER        PIC X VALUE SPACE.
           05  WS-DISP-DATA  PIC X(132).
           
       PROCEDURE DIVISION.
       MAIN-LOGIC.
           OPEN INPUT GAME-STATE LEVEL-DATA
           OPEN OUTPUT DISPLAY-FILE
           
           READ GAME-STATE
           
           PERFORM LOAD-LEVEL-DATA
           PERFORM CALCULATE-VIEWPORT
           PERFORM RENDER-VIEW
           PERFORM DISPLAY-STATUS
           
           CLOSE GAME-STATE LEVEL-DATA DISPLAY-FILE
           STOP RUN.
           
       LOAD-LEVEL-DATA.
           PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > 20
               READ LEVEL-DATA
               MOVE LEVEL-REC TO WS-MAP-ROW(WS-I)
           END-PERFORM.
           
       CALCULATE-VIEWPORT.
      *    Center viewport on player position
           COMPUTE WS-VIEW-X = PLAYER-X - 10
           COMPUTE WS-VIEW-Y = PLAYER-Y - 5
           
           IF WS-VIEW-X < 1 THEN
               MOVE 1 TO WS-VIEW-X
           END-IF
           
           IF WS-VIEW-Y < 1 THEN
               MOVE 1 TO WS-VIEW-Y
           END-IF.
           
       RENDER-VIEW.
      *    Draw border
           MOVE ALL '-' TO WS-DISP-DATA
           MOVE '+' TO WS-DISP-DATA(1:1)
           MOVE '+' TO WS-DISP-DATA(22:1)
           WRITE DISPLAY-LINE FROM WS-DISPLAY-LINE
           
      *    Draw map viewport
           PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > 10
               MOVE '|' TO WS-DISP-DATA(1:1)
               
               PERFORM VARYING WS-J FROM 1 BY 1 UNTIL WS-J > 20
                   COMPUTE WS-VIEW-X = WS-VIEW-X + WS-J - 1
                   COMPUTE WS-VIEW-Y = WS-VIEW-Y + WS-I - 1
                   
                   IF WS-VIEW-X = PLAYER-X AND WS-VIEW-Y = PLAYER-Y
                       MOVE '@' TO WS-DISP-DATA(WS-J + 1:1)
                   ELSE
                       MOVE WS-MAP-CELL(WS-VIEW-Y, WS-VIEW-X) 
                            TO WS-DISP-DATA(WS-J + 1:1)
                   END-IF
               END-PERFORM
               
               MOVE '|' TO WS-DISP-DATA(22:1)
               WRITE DISPLAY-LINE FROM WS-DISPLAY-LINE
           END-PERFORM
           
      *    Draw bottom border
           MOVE ALL '-' TO WS-DISP-DATA
           MOVE '+' TO WS-DISP-DATA(1:1)
           MOVE '+' TO WS-DISP-DATA(22:1)
           WRITE DISPLAY-LINE FROM WS-DISPLAY-LINE.
           
       DISPLAY-STATUS.
           MOVE SPACES TO WS-DISPLAY-LINE
           STRING 'HP: ' DELIMITED BY SIZE
                  PLAYER-HEALTH DELIMITED BY SIZE
                  '  AMMO: ' DELIMITED BY SIZE
                  PLAYER-AMMO DELIMITED BY SIZE
                  INTO WS-DISP-DATA
           WRITE DISPLAY-LINE FROM WS-DISPLAY-LINE
           
           MOVE 'Commands: N)orth S)outh E)ast W)est F)ire' 
                TO WS-DISP-DATA
           WRITE DISPLAY-LINE FROM WS-DISPLAY-LINE.