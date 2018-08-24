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
 * @ingroup source_interface_utils
 * This module contains the DEFINES and functions that comprise the
 * source_interface_utils library.
 *
 * @file
 * Source file for source_interface_utils library.
 *
 ****************************************************************************/
#define _GNU_SOURCE
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include "vrf-utils.h"
#include "source-interface-utils.h"
#include "vswitch-idl.h"
#include "openvswitch/vlog.h"

VLOG_DEFINE_THIS_MODULE(source_interface_utils);

/*-----------------------------------------------------------------------------
| Function         : get_configured_protocol_source
| Responsibility   : To Read source-interface configuration of a protocol
|                    on a specific VRF.
| Parameters       :
|        idl       : idl reference to OVSDB
|        type      : To specify the type of the protocol
|        vrf_name  : VRF name to use to locate the record
|    proto_source  : Structure to store the source-interface and type
| Return           : On success returns true,
|                    On failure returns false
-----------------------------------------------------------------------------*/
bool
get_configured_protocol_source(const struct ovsdb_idl *idl,
                               source_interface_protocol type,
                               const char *vrf_name,
                               protocol_source *proto_source)
{
    const struct ovsrec_vrf *vrf_row = NULL;
    int i = 0;

    if (proto_source == NULL)
    {
        return false;
    }

    /* Set default values. */
    proto_source->source = NULL;
    proto_source->config_type = SOURCE_MAX;

    if ((idl == NULL) || (vrf_name == NULL) || (type >= PROTOCOL_MAX))
    {
        return false;
    }

    vrf_row = vrf_lookup(idl, vrf_name);
    if (vrf_row == NULL)
    {
        VLOG_ERR("Unable to find %s entry in the VRF table.", vrf_name );
        return false;
    }

    /* source-ip configuration is given priority over source-interface */
    proto_source->source = (char *)smap_get(&vrf_row->source_ip,
                            protocol_keys[type]);
    if (proto_source->source == NULL) {

        for (i = 0; i < vrf_row->n_source_interface; i++) {
            if (!strncmp(protocol_keys[type], vrf_row->key_source_interface[i],
                        strlen(protocol_keys[type])))
            {
                proto_source->source =
                    vrf_row->value_source_interface[i]->name;
                proto_source->config_type = SOURCE_INTERFACE;
                return true;
            }
        }
    }
    else
    {
        proto_source->config_type = SOURCE_IP;
        return true;
    }
    return false;
}

/*-----------------------------------------------------------------------------
| Function         : get_protocol_source
| Responsibility   : Reads source-interface configuration to be used for a
|                    protocol on a given VRF. Following sequence is used in
|                    deciding the configuration to be returned (from a specific VRF)
|                    1. Protocol source-interface configuration
|                    2. NULL configuration
| Parameters       :
|        idl       : idl reference to OVSDB
|        type      : To specify the type of the protocol
|        vrf_name  : VRF name to use to locate the record
|    proto_source  : Structure to store the source-interface and type
| Return           : On success returns true,
|                    On failure returns false
-----------------------------------------------------------------------------*/
bool
get_protocol_source(const struct ovsdb_idl *idl,
                    source_interface_protocol type,
                    const char *vrf_name,
                    protocol_source *proto_source)
{
    if (get_configured_protocol_source(idl, type, vrf_name,
                                       proto_source))
    {
        return true;
    }
    if ((type != ALL_PROTOCOL) && (((get_configured_protocol_source(idl,
        ALL_PROTOCOL, vrf_name, proto_source)))))
    {
        return true;
    }
    return false;
}
