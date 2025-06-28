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
