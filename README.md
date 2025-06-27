# DOOM-COBOL Quick Start Guide

## Prerequisites

1. **Docker** - For running z/OS emulation
2. **Python 3.8+** - For the bridge service
3. **DOOM** - The original DOS game or a source port
4. **X11** (Linux) or **Windows** - For sending input to DOOM

## Step 1: Set Up z/OS Environment

```bash
# Pull Hercules MVS Docker image
docker pull rattydave/docker-ubuntu-hercules-mvs:latest

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  mainframe:
    image: rattydave/docker-ubuntu-hercules-mvs:latest
    container_name: doom-mvs
    ports:
      - "3270:3270"
      - "8038:8038"
      - "2121:21"
    volumes:
      - ./mvs-data:/hercules/data
      - ./cobol:/hercules/cobol
EOF

# Start the mainframe
docker-compose up -d
```

## Step 2: Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install psutil pyautogui python-xlib

# For Windows, also install:
# pip install pywin32
```

## Step 3: Upload COBOL Programs to MVS

```bash
# Connect via FTP
ftp localhost 2121
# Login: HERC01 / CUL8TR

# Upload COBOL source
cd /hercules/cobol
put DOOMTACT.COB 'HERC01.DOOM.COBOL(DOOMTACT)'
put DOOMREND.COB 'HERC01.DOOM.COBOL(DOOMREND)'
put DOOMMV.COB 'HERC01.DOOM.COBOL(DOOMMV)'
quit
```

## Step 4: Compile COBOL Programs

Connect to MVS via TN3270 terminal:
```bash
# Install c3270 or x3270
sudo apt-get install c3270  # or x3270 for GUI

# Connect
c3270 localhost:3270
```

Submit compilation JCL:
```jcl
//COMPILE  JOB (ACCT),'COMPILE DOOM',CLASS=A
//COBOL    EXEC COBUCLG,PARM.COB='NOLIB,APOST'
//COB.SYSIN DD DSN=HERC01.DOOM.COBOL(DOOMTACT),DISP=SHR
//GO.SYSOUT DD SYSOUT=*
```

## Step 5: Create MVS Datasets

Submit dataset allocation JCL:
```jcl
//DOOMDEFS JOB (ACCT),'DOOM DATASETS',CLASS=A
//ALLOCATE EXEC PGM=IEFBR14
//STATE    DD DSN=DOOM.STATE,DISP=(NEW,CATLG),
//            UNIT=3380,SPACE=(TRK,(1,1)),
//            DCB=(RECFM=FB,LRECL=80,BLKSIZE=3200)
//ENTITIES DD DSN=DOOM.ENTITIES,DISP=(NEW,CATLG),
//            UNIT=3380,SPACE=(TRK,(10,10)),
//            DCB=(RECFM=FB,LRECL=120,BLKSIZE=3600)
//COMMANDS DD DSN=DOOM.COMMANDS,DISP=(NEW,CATLG),
//            UNIT=3380,SPACE=(TRK,(5,5)),
//            DCB=(RECFM=FB,LRECL=80,BLKSIZE=3200)
```

## Step 6: Start DOOM

```bash
# For DOS DOOM in DOSBox
dosbox -conf doom.conf

# For source port (e.g., Chocolate Doom)
chocolate-doom -window -geometry 640x480

# For GZDoom
gzdoom -iwad doom.wad -window -width 640 -height 480
```

## Step 7: Launch the Bridge

```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Start the bridge
python bridge/doom_bridge.py --mvs-host localhost --debug
```

## Step 8: Submit DOOM Control JCL

Create the main game loop JCL:
```jcl
//DOOMLOOP JOB (ACCT),'DOOM CONTROL',CLASS=A
//LOOP     EXEC PGM=DOOMTACT
//STEPLIB  DD DSN=HERC01.DOOM.LOADLIB,DISP=SHR
//GAMESTAT DD DSN=DOOM.STATE,DISP=SHR
//ENTITIES DD DSN=DOOM.ENTITIES,DISP=SHR
//TACTICS  DD DSN=DOOM.TACTICS,DISP=(NEW,PASS)
//COMMANDS DD DSN=DOOM.COMMANDS,DISP=(NEW,CATLG)
//SYSOUT   DD SYSOUT=*
```

## Testing the Setup

1. **Verify Bridge Connection**
   - Check bridge logs for "Connected to MVS"
   - Should see "Found DOOM process"

2. **Test Simple Movement**
   - Submit a test job that writes 'KPW' to DOOM.COMMANDS
   - DOOM should move forward

3. **Monitor Execution**
   - Watch MVS job output in TN3270
   - Bridge console shows state updates
   - DOOM should respond to COBOL commands

## Troubleshooting

### "DOOM process not found"
- Make sure DOOM is running with a window title containing "doom"
- Check process name with `ps aux | grep -i doom`

### "FTP connection refused"
- Verify Docker container is running: `docker ps`
- Check port mapping: `docker port doom-mvs`

### "Dataset not found"
- Ensure datasets were allocated with correct names
- Check dataset exists: In TSO, use `LISTCAT ENT(DOOM.*)`

### "No commands executed"
- Verify DOOM.COMMANDS has records
- Check bridge is reading the correct dataset
- Ensure EBCDIC conversion is working

## Performance Tips

1. **Reduce FTP Overhead**
   - Batch multiple commands in one dataset write
   - Use binary transfer mode where possible

2. **Optimize COBOL**
   - Pre-calculate common angles
   - Use lookup tables for trig functions
   - Minimize dataset I/O

3. **Tune JCL**
   - Use high priority job class
   - Allocate sufficient region size
   - Consider multiple initiators

## Next Steps

1. **Enhance Combat AI**
   - Implement predictive aiming
   - Add weapon switching logic
   - Create dodge patterns

2. **Add Pathfinding**
   - Implement A* in COBOL
   - Use level data for navigation
   - Avoid obstacles

3. **Multi-Level Support**
   - Detect level transitions
   - Load appropriate tactics
   - Handle different enemy types

## The Dream

Once fully operational, you'll have:
- DOOM running at full speed
- COBOL making tactical decisions
- JCL orchestrating strategy
- Mainframe technology fragging demons

"Because sometimes the most beautiful code is the most absurd."