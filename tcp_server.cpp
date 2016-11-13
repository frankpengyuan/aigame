#include <cstdlib>
#include <cstdio>
#include <stdio.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/tcp.h>
#include <netinet/in.h>
#include <errno.h>
#include <string.h>
#include <iostream>
#include <unistd.h> //write
#include "tcp_server.h"

tcp_server::tcp_server(int port_num)
{
    printf("[TCP] Initializing with port: %d\n", port_num);
    this -> port = port_num;
    this -> socket_desc = socket(AF_INET, SOCK_STREAM, 0);
    this -> is_connected = false;
    int flag = 1;
    setsockopt(this -> socket_desc,IPPROTO_TCP,TCP_NODELAY,(char *)&flag,sizeof(flag));
}

tcp_server::~tcp_server()
{
    printf("[TCP] Closing connection\n");
    close(socket_desc);
    close(client_sock); // close socket when object distroyed
}

bool tcp_server::listen_to_port(int port)
{
    this -> server.sin_family = AF_INET;    // prepare for listening
    this -> server.sin_addr.s_addr = INADDR_ANY;
    this -> server.sin_port = htons( port );
    int error_msg;
    if( (error_msg = bind(socket_desc,(struct sockaddr *)&server , sizeof(server)))  < 0)
    {
        printf("[TCP] [Listen] bind failed. Error: %d\n",error_msg);
        return false;
    }
    printf("[TCP] [Listen] bind done\n");
    listen(socket_desc , SOMAXCONN);
    this -> is_connected = true;
    return true;
}

bool tcp_server::listen_and_accept()
{
    if (this -> is_connected == true)
    {
        return true;
    }
    if (listen_to_port(this -> port) == false)
    {
        printf("[TCP] listen failed!");
        return false;
    }
    //Accept and incoming connection
    printf("[TCP] [Listen] Waiting for incoming connections...\n");
    c = sizeof(struct sockaddr_in);

    //accept connection from an incoming client
    this -> client_sock = accept(socket_desc, (struct sockaddr *)&client, (socklen_t*)&c);

    if (this -> client_sock < 0)
    {
        printf("[TCP] accept connection failed\n");
        return false;
    }
    printf("[TCP] [Listen] Connection accepted\n");
    int flag = 1;
    setsockopt(this -> client_sock,IPPROTO_TCP,TCP_NODELAY,(char *)&flag,sizeof(flag));
    return true;
}

bool tcp_server::my_send(const void * start, size_t length, unsigned long count)
{
    if( send(this -> client_sock , start , length * count, 0 ) < 0) // TODO: falg:MSG_WAITALL? not sure for sending
    {
        printf("[TCP] Send failed\n");
        return false;
    }
    return true;
}

int tcp_server::my_receive(char * buffer, size_t target_length)
{
    char * rec_buffer = NULL;
    if (target_length > MAX_BUFFER_LEN)
    {
        int cnt = 0;
        rec_buffer = new char[MAX_BUFFER_LEN];
        memset(rec_buffer, 0, MAX_BUFFER_LEN);
        while(target_length > MAX_BUFFER_LEN)
        {
            int read_size = recv(this -> client_sock , rec_buffer , MAX_BUFFER_LEN , MSG_WAITALL); // wait for a full packet
            if (read_size == (int)MAX_BUFFER_LEN)
            {
                memcpy(buffer + cnt * MAX_BUFFER_LEN, rec_buffer, MAX_BUFFER_LEN);
                cnt++;
            }
            else
            {
                printf("[TCP] receive error No.2\n");
            }
            target_length -= MAX_BUFFER_LEN;
            memset(rec_buffer, 0, MAX_BUFFER_LEN);
        }
        int read_size = recv(this -> client_sock , rec_buffer , MAX_BUFFER_LEN , MSG_WAITALL); // wait for a full packet
        if (read_size == (int)target_length)
        {
            memcpy(buffer + cnt * MAX_BUFFER_LEN, rec_buffer, target_length);
            delete[] rec_buffer;
            return read_size + cnt * MAX_BUFFER_LEN;
        }
    }
    else
    {
        rec_buffer = new char[target_length];
        memset(rec_buffer, 0, target_length);
        int read_size = recv(this -> client_sock , rec_buffer , target_length , MSG_WAITALL); // wait for a full packet
        if (read_size == (int)target_length)
        {
            memcpy(buffer, rec_buffer, target_length);
            delete[] rec_buffer;
            return read_size;
        }
        printf("[TCP] receive error No.1 with rec size:%d\n", read_size);
    }
    delete[] rec_buffer;
    return 0;
}
/*
int main(int argc, char const *argv[])
{
    class::tcp_server my_server(8222);
    my_server.listen_and_accept();
    float f_array[6] = {0.1, 1.2, 515251.46653, -45156, 0, -4413.22};
    my_server.my_send(f_array, sizeof(float), 6);
    char buffer[10];
    memset(buffer, 0, 10);
    my_server.my_receive(buffer, 4);
    printf("%s\n", buffer);
    return 0;
}
*/
/*
int main()
{
    int serverSock=-1,clientSock=-1;
    struct sockaddr_in serverAddr;

    serverSock=socket(AF_INET,SOCK_STREAM,0);
    if(serverSock<0)
    {
        printf("socket creation failed\n");
        exit(-1);
    }
    printf("socket create successfully.\n");

    memset(&serverAddr,0,sizeof(serverAddr));
    serverAddr.sin_family=AF_INET;
    serverAddr.sin_port=htons((u_short) SRVPORT);
    serverAddr.sin_addr.s_addr=htons(INADDR_ANY);
    if(bind(serverSock,(struct sockaddr *) &serverAddr,sizeof(struct sockaddr_in))==-1)
    {
        printf("Bind error.\n");
        exit(-1);
    }
    printf("Bind successful.\n");

    if(listen(serverSock,10)==-1)
    {
        printf("Listen error!\n");
    }
    printf("Start to listen!\n");

    char revBuf[MAX_NUM]={0};
    char sedBuf[MAX_NUM]={0};
    while(1)
    {
        clientSock=accept(serverSock,NULL,NULL);
        while(1)
        {
        	int read_len = read(clientSock,revBuf,MAX_NUM);
            printf("read_len:%d\n", read_len);
            if(read_len==-1)
            {
                printf("read error.\n");
            }
            else
            {
                printf("Client:%s\n",revBuf);
            }
            if(strcmp(revBuf,"Quit")==0||strcmp(revBuf,"quit")==0)
            {
                strcpy(sedBuf,"Goodbye,my dear client!");
            }
            else
            {
                strcpy(sedBuf,"Hello Client.");
            }
            if(write(clientSock,sedBuf,sizeof(sedBuf))==-1)
            {
                printf("Send error!\n");
            }
            printf("Me(Server):%s\n",sedBuf);
            if(strcmp(revBuf,"Quit")==0||strcmp(revBuf,"quit")==0)
            {
                break;
            }
            bzero(revBuf,sizeof(revBuf));
            bzero(sedBuf,sizeof(sedBuf));
        }
        close(clientSock);
    }
    printf("strange!\n");
    close(serverSock);
    return 0;
}*/



/*
int main(int argc, char const *argv[])
{
	int * int_arry = new int[5];
	FILE * my_file = fopen("c.bin", "rb");
	FILE * my_file2 = fopen("c2.bin", "wb");
	fread(int_arry, sizeof(int), 5, my_file);
	fclose(my_file);
	for (int i = 0; i < 5; ++i)
	{
		printf("%d\n", int_arry[i]);
		fwrite(int_arry + 4 - i, sizeof(int), 1, my_file2);
	}
	fclose(my_file2);
	delete[] int_arry;
	return 0;
}*/