/*
 Copyright (C) 2016 Hewlett-Packard Development Company, L.P.
 All Rights Reserved.

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain
    a copy of the License at

         http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
    License for the specific language governing permissions and limitations
    under the License.
*/

/*************************************************************************//**
 * @ingroup l3_utils
 * This module contains the DEFINES and functions that comprise the l3-utils
 * library.
 *
 * @file
 * Source file for l3-utils library.
 *
 ****************************************************************************/

#include <stdio.h>
#include <unistd.h>
#include <sched.h>
#include <string.h>
#include <errno.h>
#include <byteswap.h>

#include <assert.h>
#include "vrf-utils.h"
#include "l3-utils.h"

/*
 * Function extracts and returns the subnet mask bits from ip_addr
 * Parameter 1 : IPv4 address
 */
static unsigned int
l3_utils_mask_bits (const char *ip_addr, u_char family)
{
    unsigned int mask_bits = 0;
    char *p;

    if ((p = strchr(ip_addr, '/'))) {
        mask_bits = atoi(p + 1);
    }
    /* If '/' is not present in ip_addr, it assumed its host address */
    else {
        if (family == AF_INET) {
            mask_bits = IPV4_BITLENGTH_MAX;
        }
        else if (family == AF_INET6) {
            mask_bits = IPV6_BITLENGTH_MAX;
        }
    }
    return mask_bits;
}

/*
 * This function returns the IP address part of the input IPv4
 * address without subnet mask bits.
 * Parameter 1 : IPv4 address
 */
static uint32_t
l3_utils_ipv4_address (const char* ip_addr)
{
    char ipAddressString[IP_ADDRESS_LENGTH + 1];
    uint32_t  addr = 0;
    char *p;

    strncpy(ipAddressString, ip_addr, IP_ADDRESS_LENGTH + 1);
    if (NULL != (p = (strchr(ipAddressString, '/')))) {
        *p = '\0';
    }

    inet_pton(AF_INET, ipAddressString, &addr);
    addr = htonl(addr);

    return addr;
}

/* Represents IPv6 address split into 2 64 bit integers */
struct split_ipv6_addr
{
    uint64_t start;
    uint64_t end;
};

/*
 * Function masks the IPv6 address with the subnet mask if mask_bits.
 * Returns the routing prefix (masked IPv6 addr).
 * Parameter 1 : Contains the masked IPv6 address.
 * Parameter 2 : Contains the input IPv6 address which will be masked with
 *               subnet mask.
 * Parameter 3 : Subnet mask bits.
 */
static void
l3_utils_mask_ipv6_addr (unsigned char *masked_addr, unsigned char *ipv6_addr,
                         unsigned int mask_bits)
{
    struct split_ipv6_addr parts;
    uint64_t mask = 0;
    unsigned char *p = masked_addr;

    memset(masked_addr, 0, sizeof(struct in6_addr));
    memcpy(&parts, ipv6_addr, sizeof(parts));

    if (mask_bits <= 64) {
        mask = bswap_64(bswap_64(parts.start) &
               ((uint64_t) (~0) << (64 - mask_bits)));
        memcpy(masked_addr, &mask, sizeof(uint64_t));
        return;
    }

    mask_bits -= 64;

    memcpy(masked_addr, &(parts.start), sizeof(uint64_t));
    p += sizeof(uint64_t);
    mask = bswap_64(bswap_64(parts.end) & (uint64_t) (~0) << (64 - mask_bits));
    memcpy(p, &mask, sizeof(uint64_t));
    return;
}

/*
 * This function mask subnet from the entered IPv6 address
 * using subnet bits.
 * Parameter 1 : IPv6 address
 * Parameter 2 : subnet addr contains masked IPv6 address
 * Parameter 3 : Subnet mask bits.
 */
static void
l3_utils_ipv6_subnet (const char* ip_addr, char *subnet_addr,
                      unsigned int mask_bits)
{
    char ipAddressString[IPV6_ADDRESS_LENGTH + 1];
    unsigned char ipv6_addr[sizeof(struct in6_addr)];
    unsigned char masked_addr[sizeof(struct in6_addr)];
    char *p;

    strncpy(ipAddressString, ip_addr, IPV6_ADDRESS_LENGTH + 1);
    if (NULL != (p = (strchr(ipAddressString, '/')))) {
        *p = '\0';
    }

    inet_pton(AF_INET6, ipAddressString, ipv6_addr);
    l3_utils_mask_ipv6_addr(masked_addr, ipv6_addr, mask_bits);
    inet_ntop(AF_INET6, masked_addr, subnet_addr, INET6_ADDRSTRLEN);
}

/*
 * Checks if IPv4/IPv6 address already configured as primary/secondary
 * IPv4/IPv6 address for any other interface.
 * Returns true indicating it has a duplicate/overlap network address.
 * Else, returns false indicating IP can be configured.
 */
bool
l3_utils_is_ipaddr_overlapping (const char *ip_address,
                                const char *if_name,
                                u_char addr_family,
                                bool secondary,
                                const struct ovsrec_vrf *vrf_row)
{
    size_t i, n;
    const struct ovsrec_port *port_row = NULL;
    char input_ipv6_subnet[INET6_ADDRSTRLEN];
    char port_ipv6_subnet[INET6_ADDRSTRLEN];
    uint32_t input_ipv4_addr = 0, port_ipv4_addr = 0, mask = 0;
    unsigned int input_mask_bits = 0, port_mask_bits = 0, mask_bits = 0;


    input_mask_bits = l3_utils_mask_bits(ip_address, addr_family);
    for (i = 0; i < vrf_row->n_ports; i++) {
        port_row = vrf_row->ports[i];
        if (addr_family == AF_INET6) {
            /* Checks if the IP is configured as primary */
            if (port_row->ip6_address != NULL ) {
                port_mask_bits = l3_utils_mask_bits(port_row->ip6_address,
                                                    addr_family);
                mask_bits = input_mask_bits < port_mask_bits ?
                            input_mask_bits : port_mask_bits;
                l3_utils_ipv6_subnet(ip_address, input_ipv6_subnet, mask_bits);
                l3_utils_ipv6_subnet(port_row->ip6_address, port_ipv6_subnet,
                                     mask_bits);
                /* Compares if 2 IPv6 subnet mask are same */
                if (!strncmp(input_ipv6_subnet, port_ipv6_subnet,
                             INET6_ADDRSTRLEN)) {
                    if (strncmp(port_row->name, if_name, strlen(if_name)) == 0) {
                        /* If input IP is secondary IP and matched with
                           primary IP, IP cannot be configured. Return true */
                        if (secondary) {
                           return true;
                        }
                        return false;
                    }
                    /* If same as another interface IP address, return true */
                    else {
                        return true;
                    }
                }
            }
            /* Loop through secondary addresses to check if any IP matches */
            if (port_row->ip6_address_secondary != NULL ) {
                for (n = 0; n < port_row->n_ip6_address_secondary; n++) {
                    port_mask_bits =
                        l3_utils_mask_bits(port_row->ip6_address_secondary[n],
                                           addr_family);
                    mask_bits = input_mask_bits < port_mask_bits ?
                                input_mask_bits : port_mask_bits;
                    l3_utils_ipv6_subnet(ip_address, input_ipv6_subnet,
                                         mask_bits);
                    l3_utils_ipv6_subnet(port_row->ip6_address_secondary[n],
                                         port_ipv6_subnet, mask_bits);

                    /* Checks if the IP is configured as secondary */
                    if (!strncmp(input_ipv6_subnet, port_ipv6_subnet,
                                 INET6_ADDRSTRLEN)) {
                        return true;
                    }
                }
            }
        }
        else if (addr_family == AF_INET) {

            input_ipv4_addr = l3_utils_ipv4_address(ip_address);

            if (port_row->ip4_address != NULL ) {
                port_ipv4_addr = l3_utils_ipv4_address(port_row->ip4_address);
                port_mask_bits = l3_utils_mask_bits(port_row->ip4_address,
                                                    addr_family);
                mask_bits = input_mask_bits < port_mask_bits ?
                            input_mask_bits : port_mask_bits;
                mask = (IPV4_SUBNET_MASK_FULL <<
                       (IPV4_ADDR_BIT_LENGTH - mask_bits));

                /* Checks if IP is same as primary IP */
                if ((input_ipv4_addr & mask) == (port_ipv4_addr & mask)) {
                    /* If IP is same and same interface, then can be confgured
                       if input is primary, else cannot be configured. */
                    if (strncmp(port_row->name, if_name, strlen(if_name))
                        == 0) {
                        if (secondary) {
                           return true;
                        }
                        return false;
                    }
                    /* Checks if IP is same as primary IP of other interface */
                    else {
                        return true;
                    }
                }
            }
            if (port_row->ip4_address_secondary != NULL ) {
                /* Loops through all the secondary addresses */
                for (n = 0; n < port_row->n_ip4_address_secondary; n++) {
                    port_ipv4_addr =
                     l3_utils_ipv4_address(port_row->ip4_address_secondary[n]);
                    port_mask_bits =
                       l3_utils_mask_bits (port_row->ip4_address_secondary[n],
                                           addr_family);
                    mask_bits = input_mask_bits < port_mask_bits ?
                                input_mask_bits : port_mask_bits;
                    mask = (IPV4_SUBNET_MASK_FULL <<
                           (IPV4_ADDR_BIT_LENGTH - mask_bits));
                    /* Checks if any secondary IP address matches */
                    if ((input_ipv4_addr & mask) == (port_ipv4_addr & mask)) {
                        return true;
                    }
                }
            }
        }
    }
    return false;
}
