//DOOMLOOP JOB (ACCT),'DOOM MAIN LOOP',CLASS=A,MSGCLASS=X
//*
//* Main DOOM control loop - runs continuously
//*
//LOOP     EXEC PGM=DOOMTACT
//STEPLIB  DD DSN=DOOM.LOADLIB,DISP=SHR
//GAMESTAT DD DSN=DOOM.STATE,DISP=SHR
//ENTITIES DD DSN=DOOM.ENTITIES,DISP=SHR
//TACTICS  DD DSN=DOOM.TACTICS,DISP=(NEW,PASS)
//COMMANDS DD DSN=DOOM.COMMANDS,DISP=(MOD,KEEP)
//SYSOUT   DD SYSOUT=*
//*