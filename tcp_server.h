#include <cstdlib>
#include <cstdio>
#include <stdio.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <errno.h>
#include <string.h>
#include <iostream>
#include <unistd.h>    //write

#ifndef __TCP_SERVER__
#define __TCP_SERVER__

#define SRVPORT 8221
#define CONNECT_NUM 1
#define MAX_BUFFER_LEN 1000

#define AMMO_T_SIZE 17
#define ENEMY_SHIP_T_SIZE 17
#define HERO_INFO_T_SIZE 36

struct ammo_t
{
    float pos[2];
    float speed[2];
    char type;
};

struct enemy_ship_t
{
    float pos[2];
    char type;
};

struct hero_info_t
{
    float pos[2];
    float taken_dmg;
    float lives;
    float gun1;
    float gun2;
    float gun3;
    float shield;
    float score;
};

class tcp_server
{
public:
    tcp_server(int port_num = SRVPORT);
    ~tcp_server();
    bool listen_to_port(int port);
    bool listen_and_accept();   // open the port for listening
    bool my_send(const void * start, size_t length, unsigned long count);    // general send, send one packet
    int my_receive(char * buffer, size_t target_length);
    bool is_connected;
private:
    int port;
    char ip[20];
    int c, socket_desc, client_sock;
    struct sockaddr_in client, server;
};

#endif

