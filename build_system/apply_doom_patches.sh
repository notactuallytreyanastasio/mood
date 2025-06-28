#!/bin/bash
# Apply DOOM patches manually

set -e

WORK_DIR="$1"
if [ -z "$WORK_DIR" ]; then
    echo "Usage: $0 <doom_source_dir>"
    exit 1
fi

cd "$WORK_DIR"

echo "Applying state export patches..."

# 1. Add x_state.c to Makefile
if ! grep -q "x_state.o" Makefile; then
    echo "Patching Makefile..."
    sed -i.bak 's/st_stuff.o$/st_stuff.o \\/' Makefile
    echo -e '\tx_state.o' >> Makefile
fi

# 2. Add include to g_game.c
if ! grep -q "x_state.h" g_game.c; then
    echo "Patching g_game.c..."
    # Add include after other includes
    sed -i.bak '/#include "s_sound.h"/a\
#include "x_state.h"' g_game.c
    
    # Add export call in G_Ticker
    # Find G_Ticker and add after the opening brace
    perl -i.bak -pe 'if (/^void G_Ticker\s*\(void\)/) { $found = 1; } 
                     if ($found && /^{/) { 
                         $_ .= "\n    // Export game state\n    X_ExportState();\n"; 
                         $found = 0; 
                     }' g_game.c
fi

# 3. Create x_state.h
cat > x_state.h << 'EOF'
#ifndef __X_STATE__
#define __X_STATE__

void X_ExportState(void);
void X_InitState(void);

#endif
EOF

# 4. Create x_state.c
cat > x_state.c << 'EOF'
// State export for DOOM-COBOL integration

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#include "doomdef.h"
#include "doomstat.h"
#include "d_player.h"
#include "p_local.h"
#include "m_fixed.h"

#define STATE_PORT 31337
#define STATE_MAGIC 0x4D4F4F44  // 'DOOM'
#define STATE_VERSION 1

static int state_socket = -1;
static struct sockaddr_in state_addr;
static FILE* cobol_file = NULL;

typedef struct {
    uint32_t magic;
    uint32_t version;
    uint32_t tick;
    
    // Player state
    int32_t health;
    int32_t armor;
    int32_t ammo[NUMAMMO];
    int32_t weapon;
    int32_t x, y, z;
    uint32_t angle;
    int32_t momx, momy;
    
    // Game state
    int32_t level;
    int32_t kills;
    int32_t items;
    int32_t secrets;
    int32_t enemy_count;
    
} state_packet_t;

void X_InitState(void) {
    // Create UDP socket
    state_socket = socket(AF_INET, SOCK_DGRAM, 0);
    if (state_socket < 0) {
        fprintf(stderr, "X_InitState: Failed to create socket\n");
        return;
    }
    
    // Setup address
    memset(&state_addr, 0, sizeof(state_addr));
    state_addr.sin_family = AF_INET;
    state_addr.sin_port = htons(STATE_PORT);
    state_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
    
    printf("X_InitState: State export initialized on port %d\n", STATE_PORT);
}

void X_ExportState(void) {
    player_t* plyr;
    state_packet_t packet;
    int i;
    
    if (!players[consoleplayer].mo)
        return;
        
    plyr = &players[consoleplayer];
    
    // Fill packet
    memset(&packet, 0, sizeof(packet));
    packet.magic = STATE_MAGIC;
    packet.version = STATE_VERSION;
    packet.tick = gametic;
    
    // Player info
    packet.health = plyr->health;
    packet.armor = plyr->armorpoints;
    packet.weapon = plyr->readyweapon;
    
    for (i = 0; i < NUMAMMO; i++)
        packet.ammo[i] = plyr->ammo[i];
        
    // Position
    packet.x = plyr->mo->x;
    packet.y = plyr->mo->y;
    packet.z = plyr->mo->z;
    packet.angle = plyr->mo->angle;
    packet.momx = plyr->mo->momx;
    packet.momy = plyr->mo->momy;
    
    // Level info
    packet.level = gameepisode * 10 + gamemap;
    packet.kills = plyr->killcount;
    packet.items = plyr->itemcount;
    packet.secrets = plyr->secretcount;
    
    // Send UDP packet
    if (state_socket >= 0) {
        sendto(state_socket, &packet, sizeof(packet), 0,
               (struct sockaddr*)&state_addr, sizeof(state_addr));
    }
    
    // Also write COBOL format
    if (!cobol_file) {
        cobol_file = fopen("/tmp/doom_state.dat", "w");
    }
    
    if (cobol_file) {
        fprintf(cobol_file, "STATE   %08d%02d%08d\n",
                packet.tick, packet.level, (int)time(NULL));
        fprintf(cobol_file, "PLAYER  %+08d%+08d%+08d%+04d%03d%03d%c\n",
                packet.x >> 16, packet.y >> 16, packet.z >> 16,
                (int)(packet.angle * 360.0 / 0xFFFFFFFF),
                packet.health, packet.armor,
                packet.health > 0 ? 'A' : 'D');
        fprintf(cobol_file, "AMMO    %04d%04d%04d%04d%01d\n",
                packet.ammo[0], packet.ammo[1], 
                packet.ammo[2], packet.ammo[3],
                packet.weapon);
        fflush(cobol_file);
    }
}
EOF

# 5. Add network input patches
if ! grep -q "N_InitNetworkInput" d_main.c; then
    echo "Patching d_main.c for network input..."
    
    # Add extern declaration before D_DoomMain
    perl -i.bak -pe 'if (/^void D_DoomMain/) { 
                         print "// Network input\nextern void N_InitNetworkInput(void);\n\n"; 
                     }' d_main.c
    
    # Add init call
    sed -i.bak '/I_InitGraphics/a\
    N_InitNetworkInput();' d_main.c
fi

# 6. Create n_input.c
cat > n_input.c << 'EOF'
// Network input for DOOM

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <pthread.h>

#include "doomdef.h"
#include "d_event.h"

#define INPUT_PORT 31338

static int input_socket = -1;
static pthread_t input_thread;

static void* N_InputThread(void* arg) {
    struct sockaddr_in addr;
    char buffer[256];
    int len;
    
    while (1) {
        len = recv(input_socket, buffer, sizeof(buffer)-1, 0);
        if (len > 0) {
            buffer[len] = 0;
            
            // Parse simple commands
            if (strncmp(buffer, "KEY ", 4) == 0) {
                event_t event;
                event.type = ev_keydown;
                
                if (strcmp(buffer+4, "UP") == 0)
                    event.data1 = KEY_UPARROW;
                else if (strcmp(buffer+4, "DOWN") == 0)
                    event.data1 = KEY_DOWNARROW;
                else if (strcmp(buffer+4, "LEFT") == 0)
                    event.data1 = KEY_LEFTARROW;
                else if (strcmp(buffer+4, "RIGHT") == 0)
                    event.data1 = KEY_RIGHTARROW;
                else if (strcmp(buffer+4, "FIRE") == 0)
                    event.data1 = KEY_RCTRL;
                else if (strcmp(buffer+4, "USE") == 0)
                    event.data1 = ' ';
                else if (strcmp(buffer+4, "ESCAPE") == 0)
                    event.data1 = KEY_ESCAPE;
                else if (strcmp(buffer+4, "ENTER") == 0)
                    event.data1 = KEY_ENTER;
                    
                D_PostEvent(&event);
            }
        }
    }
    
    return NULL;
}

void N_InitNetworkInput(void) {
    struct sockaddr_in addr;
    
    // Create socket
    input_socket = socket(AF_INET, SOCK_DGRAM, 0);
    if (input_socket < 0) {
        fprintf(stderr, "N_InitNetworkInput: Failed to create socket\n");
        return;
    }
    
    // Bind to port
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(INPUT_PORT);
    addr.sin_addr.s_addr = INADDR_ANY;
    
    if (bind(input_socket, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        fprintf(stderr, "N_InitNetworkInput: Failed to bind port %d\n", INPUT_PORT);
        close(input_socket);
        input_socket = -1;
        return;
    }
    
    // Start thread
    pthread_create(&input_thread, NULL, N_InputThread, NULL);
    
    printf("N_InitNetworkInput: Network input initialized on port %d\n", INPUT_PORT);
}
EOF

# 7. Update Makefile for new files
if ! grep -q "n_input.o" Makefile; then
    echo "Adding n_input.o to Makefile..."
    sed -i.bak 's/x_state.o$/x_state.o \\/' Makefile
    echo -e '\tn_input.o' >> Makefile
fi

# 8. Add initialization call
if ! grep -q "X_InitState" d_main.c; then
    echo "Adding X_InitState to d_main.c..."
    sed -i.bak '/N_InitNetworkInput/a\
    X_InitState();' d_main.c
fi

echo "Patches applied successfully!"
echo "You may need to link with -lpthread for network input"