/*
 *(c) Copyright 2015-2016 Hewlett Packard Enterprise Development LP.
 *
 *   Licensed under the Apache License, Version 2.0 (the "License"); you may
 *   not use this file except in compliance with the License. You may obtain
 *   a copy of the License at
 *
 *        http://www.apache.org/licenses/LICENSE-2.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 *   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 *   License for the specific language governing permissions and limitations
 *   under the License.
 *
 * File:ping_send.c
*/

#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/ip_icmp.h>
#include <netinet/icmp6.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include "openvswitch/vlog.h"
#include "ops-utils.h"

#define DEFDATALEN  56
#define MAXICMPLEN 76
#define MAXIPLEN  60

#define PACKETSIZE  64

VLOG_DEFINE_THIS_MODULE(ping_util);

struct packet
{
    struct icmphdr hdr;
    char msg[PACKETSIZE-sizeof(struct icmphdr)];
};

/*This function creates a socket to send icmp packet
* socket_family = AF_INET6
* socket_type = SOCK_RAW
* protocol = IPPROTO_ICMPV6
*/
static int create_icmp6_socket(void)
{
    int sock;
    sock = socket(AF_INET6, SOCK_RAW, IPPROTO_ICMPV6);
    return sock;
}

/*--------------------------------------------------------------------
*--- checksum - standard 1s complement checksum                   ---
*--------------------------------------------------------------------*/
unsigned short checksum(void *b, int len)
{   unsigned short *buf = b;
    unsigned int sum=0;
    unsigned short result;

    for ( sum = 0; len > 1; len -= 2 )
        sum += *buf++;
    if ( len == 1 )
        sum += *(unsigned char*)buf;
    sum = (sum >> 16) + (sum & 0xFFFF);
    sum += (sum >> 16);
    result = ~sum;
    return result;
}

/*This function creates a socket to send icmp packet
* socket_family = AF_INET
* socket_type = SOCK_RAW
* protocol = IPPROTO_ICMP
*/
static int create_icmp4_socket(void)
{
    int sock;
    sock = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP);
    return sock;
}

/*This function sends a ICMP_ECHO packet to the target.
* target must be a ipv4 address string.
*/
int ping4(const char *target)
{
    struct sockaddr_in pingaddr;
    struct packet pckt;
    const int val=255;
    int pingsock;
    int err = -1;
    if((pingsock = create_icmp4_socket())< 0){
        VLOG_ERR("can not create icmp4_socket. errstr = %s",strerror(errno));
        return pingsock;
    }
    if ((err = setsockopt(pingsock, SOL_IP, IP_TTL, &val, sizeof(val))) != 0){
        VLOG_ERR("Set TTL option");
        close(pingsock);
        return err;
    }

    memset(&pingaddr, 0, sizeof(struct sockaddr_in));
    pingaddr.sin_family = AF_INET;
    if((err = inet_pton(AF_INET, target, &pingaddr.sin_addr)) <= 0){
        VLOG_ERR("The given target_ip_add is not valid. error: %d",err);
        close(pingsock);
        return err;
    }

    memset(&pckt, 0, sizeof(pckt));
    pckt.hdr.type = ICMP_ECHO;
    pckt.hdr.un.echo.id = 1234;
    pckt.hdr.un.echo.sequence = 1;
    pckt.hdr.checksum = checksum(&pckt, sizeof(pckt));

    if ((err = sendto(pingsock, &pckt, sizeof(pckt), MSG_DONTWAIT,
                 (struct sockaddr*)&pingaddr, sizeof(pingaddr))) <= 0 ){
        VLOG_ERR("error:sendto: errstr = %s",strerror(errno) );
        close(pingsock);
        return err;
    }
    close(pingsock);
    return 0;
}


/*This function sends a ICMP6_ECHO_REQUEST packet to the target.
* target must be the ipv6 address string.
*/
int ping6(const char *target)
{
    struct sockaddr_in6 pingaddr;
    struct icmp6_hdr *pkt;
    int pingsock, c;
    int sockopt;
    int err;
    char packet[DEFDATALEN + MAXIPLEN + MAXICMPLEN];

    if((pingsock = create_icmp6_socket())< 0){
        VLOG_ERR("can not create icmp6_socket. errstr = %s",strerror(errno));
        return pingsock;
    }
    memset(&pingaddr, 0, sizeof(struct sockaddr_in));
    pingaddr.sin6_family = AF_INET6;

    if((err = inet_pton(AF_INET6, target, &pingaddr.sin6_addr)) <= 0){
        VLOG_ERR("The given target_ip_add is not valid. error: %d",err);
        return err;
    }

    pkt = (struct icmp6_hdr *) packet;
    memset(pkt, 0, sizeof(packet));
    pkt->icmp6_type = ICMP6_ECHO_REQUEST;

    sockopt = 2;
    setsockopt(pingsock, SOL_RAW, IPV6_CHECKSUM, (char *) &sockopt,
               sizeof(sockopt));

    c = sendto(pingsock, packet, sizeof(packet), MSG_DONTWAIT,
               (struct sockaddr *) &pingaddr, sizeof(struct sockaddr_in6));

    if (c < 0 ) {
        VLOG_ERR("error:sendto: errno = %s",strerror(errno) );
        close(pingsock);
        return c;
    }
    return 0;
}
