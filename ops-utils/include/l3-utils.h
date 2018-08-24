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

/***************************************************************************
 * @defgroup l3_utils Core Utilities
 * This library provides common utility functions used by various OpenSwitch
 * processes.
 * @{
 *
 * @defgroup l3_utils_public Public Interface
 * Public API for l3_utils library.
 *
 * Set of utility functions supporting Basic L3 and Port daemon functionality.
 * @{
 *
 * @file
 * Header for l3_utils library.
 ***************************************************************************/

#ifndef __L3_UTILS_H_
#define __L3_UTILS_H_

/* IP_ADDRESS is of format xxx.xxx.xxx.xxx/MM and max length 18*/
#define IP_ADDRESS_LENGTH              18
/* IPV6_ADDRESS is of format xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:AAA.BBB.CCC.DDD/MMM
   and max length is 49*/
#define IPV6_ADDRESS_LENGTH            49
#define IPV4_ADDR_BIT_LENGTH           32
#define IPV4_SUBNET_MASK_FULL          0xFFFFFFFF

#define IPV4_BITLENGTH_MAX             32
#define IPV6_BITLENGTH_MAX             128

/************************************************************************//**
 * Checks if IPv4 or IPv6 address already configured or not.
 *
 * @param[in]  ip_address: User configured ip address
 * @param[in]  if_name   : Interface for which user is configuring IP
 * @param[in]  ipv6      : 1 indicates IPv6 address, 0 IPv4 address
 * @param[in]  secondary : 1 indicates IP is configured as secondary,
		           0 as primary IP address.
 * @param[in]  vrf_row   : VRF row to which interface belongs to.
 *
 * @return 1 if input ip/ipv6 address is duplicate else 0.
 ***************************************************************************/
extern bool
l3_utils_is_ipaddr_overlapping (const char *ip_address,
                                const char *if_name,
                                u_char addr_family,
                                bool secondary,
                                const struct ovsrec_vrf *vrf_row);

#endif /* __L3_UTILS_H_ */
/** @} end of group l3_utils_public */
/** @} end of group l3_utils */
