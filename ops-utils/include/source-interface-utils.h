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

/************************************************************************//**
 * @defgroup source_interface_utils Core Utilities
 * This library provides common utility functions used by various OpenSwitch
 * processes.
 * @{
 *
 * @defgroup source_interface_utils_public Public Interface
 * Public API for source_interface_utils library.
 *
 *
 * @{
 *
 * @file
 * Header for source_interface_utils library.
 ***************************************************************************/

#ifndef __SOURCE_INTERFACE_UTILS_H_
#define __SOURCE_INTERFACE_UTILS_H_

#include "vswitch-idl.h"
#include "openswitch-idl.h"

/* FIXME: Will be removed once the macros got merged into openswitch-idl.h */
#define VRF_SOURCE_IP_MAP_TACACS            "tacacs"
#define VRF_SOURCE_INTERFACE_MAP_TACACS     "tacacs"
#define VRF_SOURCE_IP_MAP_RADIUS            "radius"
#define VRF_SOURCE_INTERFACE_MAP_RADIUS     "radius"

/* Defining the type of configuration */
typedef enum {
    SOURCE_IP,
    SOURCE_INTERFACE,
    SOURCE_MAX
}configuration_type;

/* Structure to store source-interface configuration and type. */
typedef struct proto_source_t {
    char *source;
    configuration_type config_type;
} protocol_source;

/* Defining the type of Source interface protocols passing through the cli */
typedef enum {
    TFTP_PROTOCOL,
    TACACS_PROTOCOL,
    RADIUS_PROTOCOL,
    ALL_PROTOCOL,
    PROTOCOL_MAX
}source_interface_protocol;

/* source-interface protocol keys */
static char *protocol_keys[PROTOCOL_MAX] = {
    VRF_SOURCE_INTERFACE_MAP_TFTP,
    VRF_SOURCE_INTERFACE_MAP_TACACS,
    VRF_SOURCE_INTERFACE_MAP_RADIUS,
    VRF_SOURCE_INTERFACE_MAP_ALL
};
/************************************************************************//**
 * Reads source-interface configuration of a protocol on a specific VRF.
 * source-ip configuration is given priority over source-interface.
 * @param[in]  idl          : idl reference to OVSDB
 * @param[in]  type         : To specify the type of the protocol
 * @param[in]  vrf_name     : VRF name to use to locate the record
 * @param[out]  proto_source : protocol_source reference to source-interface
 *
 * @return true if sucessful, else false on failure
 ***************************************************************************/
bool
get_configured_protocol_source(const struct ovsdb_idl *idl,
                               source_interface_protocol type,
                               const char *vrf_name,
                               protocol_source *proto_source);

/************************************************************************//**
 * Reads source-interface configuration to be used for a protocol on a given VRF.
 * Following sequence is used in deciding the configuration to be
 * returned (from a specific VRF)
 * 1. Protocol source-interface configuration
 * 2. NULL configuration
 * source-ip configuration is given priority over source-interface.

 * @param[in]  idl          : idl reference to OVSDB
 * @param[in]  type         : To specify the type of the protocol
 * @param[in]  vrf_name     : VRF name to use to locate the record
 * @param[out]  proto_source : protocol_source reference to source-interface
 *
 * @return true if sucessful, else false on failure
 ***************************************************************************/
bool
get_protocol_source(const struct ovsdb_idl *idl,
                    source_interface_protocol type, const char *vrf_name,
                    protocol_source *proto_source);

#endif /*__SOURCE_INTERFACE_UTILS_H_ */
/** @} end of group source_interface_utils_public */
/** @} end of group source_interface_utils */
