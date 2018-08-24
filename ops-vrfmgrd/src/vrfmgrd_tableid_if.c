/*
 * (c) Copyright 2016 Hewlett Packard Enterprise Development LP
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */
/************************************************************************//**
 * @ingroup vrfmgrdd
 *
 * @file
 * Source for vrfmgrd table_id generation.
 *
 ***************************************************************************/

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <errno.h>
#include <getopt.h>
#include <limits.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include "ovsdb-idl.h"
#include "vswitch-idl.h"
#include "openvswitch/vconn.h"
#include "openvswitch/vlog.h"
#include "vrfmgrd.h"

VLOG_DEFINE_THIS_MODULE(vrfmgrd_tableid_if);

struct free_vrf_id_
{
   uint32_t id;
   bool     id_available;
}free_vrf_id[MAX_VRF_ID + 1];
uint32_t used_vrf_id_num = MIN_VRF_ID;

/*
 * Intialise the Free VRF Id list during the VRF init.
 */
void initialize_free_vrf_id_list()
{
    uint32_t vrf_id = 0;
    free_vrf_id[DEFAULT_VRF_ID].id = DEFAULT_VRF_ID;
    free_vrf_id[DEFAULT_VRF_ID].id_available = false;

    for(vrf_id = MIN_VRF_ID; vrf_id <= MAX_VRF_ID; vrf_id++)
    {
        free_vrf_id[vrf_id].id = vrf_id;
        free_vrf_id[vrf_id].id_available = true;
    }
}

/*
 * Gives the first available table_Id from free_vrf_id array.
 * Global variable "used_vrf_id_num" is used as a pointer to the
 * recently used table_id index. This is to ensure that when a
 * VRF gets deleted and added again, the same VRF-ID will not be
 * allotted again and also to avoid the overhead of looping from
 * the begining everytime a table_id assign request is recieved.
 * Once the MAX_VRF_ID is reached search begins from the start to
 * see if any of the previously allocated table_id's are available.
 */
static int64_t get_available_id()
{
    int64_t vrf_id = 0;
    for(vrf_id = used_vrf_id_num; vrf_id <= MAX_VRF_ID; vrf_id++)
    {
        if(free_vrf_id[vrf_id].id_available)
        {
            used_vrf_id_num = vrf_id;
            return vrf_id;
        }
    }

    for(vrf_id = MIN_VRF_ID; vrf_id < used_vrf_id_num; vrf_id++)
    {
        if(free_vrf_id[vrf_id].id_available)
        {
            used_vrf_id_num = vrf_id;
            return vrf_id;
        }
    }
    return -1;
}

/*
 * ALLOCATE FIRST AVAILABLE VRF ID
 */
int32_t allocate_first_vrf_id(struct ovsrec_vrf *vrf)
{
    int64_t vrf_id;

    vrf_id = get_available_id();
    if(vrf_id < MIN_VRF_ID)
    {
        VLOG_DBG("table_id allocation failed for VRF %s ", vrf->name);
        return -1;
    }
    ovsrec_vrf_set_table_id(vrf, &vrf_id, sizeof(vrf_id));
    free_vrf_id[vrf_id].id_available = false;
    return vrf_id;
}

/*
 * During the process restart the VRF has table_id already assigned.
 * This function is called to update the local VRF list
 */
void set_vrf_id(int64_t vrf_id)
{
    free_vrf_id[vrf_id].id_available = false;
    return;
}

/*
 * ALLOCATE A SPECFIC VRF-ID
 */
bool allocate_vrf_id(struct ovsrec_vrf *vrf, uint32_t vrf_id)
{
    const int64_t table_id = vrf_id;

    if(vrf_id > MAX_VRF_ID)
    {
        VLOG_ERR("Requested a VRF table_id '%d' greater then Max allowed "
                 "value for VRF '%s'", vrf_id, vrf->name);
        return false;
    }

    if(free_vrf_id[vrf_id].id_available)
    {
        free_vrf_id[vrf_id].id_available = false;
        ovsrec_vrf_set_table_id(vrf, &table_id, sizeof(vrf_id));
        return true;
    }
    return false;
}

/*
 * Free the table_id and mark the ID be available. This function is called
 * during the VRF deletion.
 */
bool free_vrf_allocated_id(uint32_t vrf_id)
{
    if(vrf_id > MAX_VRF_ID)
    {
        VLOG_ERR("Recieved to free a VRF table_id '%d' greater then Max "
                 "allowed value", vrf_id);
        assert(0);
        return false;
    }

    if(free_vrf_id[vrf_id].id_available)
    {
        VLOG_ERR("Trying to free an unassigned vrf table_id: '%d'", vrf_id);
        assert(0);
        return false;
    }
    else
    {
        free_vrf_id[vrf_id].id_available = true;
        return true;
    }
}
