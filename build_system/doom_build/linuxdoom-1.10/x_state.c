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
