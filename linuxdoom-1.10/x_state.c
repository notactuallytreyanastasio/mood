// State export for DOOM
// Dumps game state every frame

#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#include "doomdef.h"
#include "doomstat.h"
#include "d_player.h"

static FILE* state_file = NULL;
static int tick_count = 0;

void X_InitState(void)
{
    printf("X_InitState: State export initialized\n");
}

void X_ExportState(void)
{
    player_t* plyr;
    
    if (!players[consoleplayer].mo)
        return;
        
    plyr = &players[consoleplayer];
    tick_count++;
    
    // Open file if not already open
    if (!state_file) {
        state_file = fopen("/tmp/doom_state.txt", "w");
        if (!state_file) {
            printf("Failed to open state file\n");
            return;
        }
    }
    
    // Write state
    fprintf(state_file, "TICK=%d HEALTH=%d ARMOR=%d X=%d Y=%d ANGLE=%d\n",
            tick_count,
            plyr->health,
            plyr->armorpoints,
            plyr->mo->x >> 16,  // Convert from fixed point
            plyr->mo->y >> 16,
            plyr->mo->angle >> 24);  // Convert angle
            
    fflush(state_file);
    
    // Also print to console every 35 ticks (1 second)
    if (tick_count % 35 == 0) {
        printf("STATE: tick=%d health=%d pos=(%d,%d)\n", 
               tick_count, plyr->health,
               plyr->mo->x >> 16, plyr->mo->y >> 16);
    }
}