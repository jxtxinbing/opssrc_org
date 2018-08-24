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
 * @ingroup vrf_utils
 * This module contains the DEFINES and functions that comprise the vrf-utils
 * library.
 *
 * @file
 * Source file for vrf-utils library.
 *
 ****************************************************************************/
#define _GNU_SOURCE
#include <stdio.h>
#include <unistd.h>
#include <sched.h>
#include <string.h>
#include <errno.h>

#include <assert.h>
#include <sys/wait.h>
#include "vrf-utils.h"
#include "vswitch-idl.h"
#include "openswitch-idl.h"
#include "openvswitch/vlog.h"

VLOG_DEFINE_THIS_MODULE(vrf_utils);
/************************************************************************//**
 * Reads the vrf row from a ovsdb based on vrf name.
 *
 * @param[in]  vrf_name  :VRF name to use to locate the record
 * @param[in]  idl       : idl reference to OVSDB
 *
 * @return row if sucessful, else NULL on failure
 ***************************************************************************/

const struct ovsrec_vrf *
vrf_lookup (const struct ovsdb_idl *idl, const char *vrf_name)
{
    const struct ovsrec_vrf *vrf_row = NULL;
    OVSREC_VRF_FOR_EACH (vrf_row, idl)
      {
        if (strncmp (vrf_row->name, vrf_name, OVSDB_VRF_NAME_MAXLEN) == 0)
        return vrf_row;
      }
    return NULL;
}/*vrf_lookup*/


/************************************************************************//**
 * Returns the default vrf row from a ovsdb.
 *
 * @param[in]  idl       : idl reference to OVSDB
 *
 * @return row if sucessful, else NULL on failure
 ***************************************************************************/
const struct ovsrec_vrf *
get_default_vrf (const struct ovsdb_idl *idl)
{
    /** TBD, Logic can be simplified further if we can store default VRF UUID.*/
    const struct ovsrec_vrf *vrf_row = vrf_lookup(idl, DEFAULT_VRF_NAME);

    return vrf_row;
}

/************************************************************************//**
 * Returns the vrf row from a ovsdb based on vrf table_id.
 *
 * @param[in]  idl       : idl reference to OVSDB
 * @param[in]  table_id  : VRF table_id to use to locate the record
 *
 * @return row if sucessful, else NULL on failure
 ***************************************************************************/
const struct ovsrec_vrf *
vrf_lookup_on_table_id (const struct ovsdb_idl *idl, const int64_t table_id)
{
    const struct ovsrec_vrf *vrf_row = NULL;
    OVSREC_VRF_FOR_EACH (vrf_row, idl)
    {
        if((vrf_row->table_id) && (*(vrf_row->table_id) == table_id))
            return vrf_row;
    }
    return NULL;
}/*vrf_lookup_on_table_id*/

/************************************************************************//**
 * Returns the VRF namespace name from an ovsdb based on vrf_name.
 * for default vrf, it always returns swns namespace as it is default.
 *
 * @param[in]  idl       : idl reference to OVSDB
 * @param[in]  vrf_name  : VRF name to use to locate the VRF record
 * @param[in,out]  vrf_ns_name  : namespace name to be filled from VRF.
 *
 * @return 0 if sucessful, else negetive on failure
 ***************************************************************************/
int
get_vrf_ns_from_name (const struct ovsdb_idl *idl, const char* vrf_name,
                      char* vrf_ns_name)
{
    const struct ovsrec_vrf *vrf_row = NULL;

    if (!is_nondefault_vrf(vrf_name))
    {
        /* DEFAULT namespace will return table_id 0 */
        snprintf(vrf_ns_name, strlen(SWITCH_NAMESPACE)+1, "%s", SWITCH_NAMESPACE);
        return 0;
    }
    vrf_row = vrf_lookup(idl, vrf_name);
    if (vrf_row != NULL)
    {
        snprintf(vrf_ns_name, UUID_LEN+1, UUID_FMT, UUID_ARGS(&(vrf_row->header_.uuid)));
        return 0;
    }

    return -1;
}

/************************************************************************//**
 * Returns the VRF namespace name from an ovsdb based on table_id.
 * for table_id 0, it always returns swns namespace as it is default.
 *
 * @param[in]  idl       : idl reference to OVSDB
 * @param[in]  table_id  : VRF table_id to use to locate the VRF record
 * @param[in,out]  vrf_ns_name  : namespace name to be filled from VRF.
 *
 * @return 0 if sucessful, else negetive on failure
 ***************************************************************************/
int
get_vrf_ns_from_table_id (const struct ovsdb_idl *idl, const int64_t table_id,
                          char* vrf_ns_name)
{
    const struct ovsrec_vrf *vrf_row = NULL;

    if (!table_id)
    {
        /* DEFAULT namespace will return table_id 0 */
        snprintf(vrf_ns_name, strlen(SWITCH_NAMESPACE)+1, "%s", SWITCH_NAMESPACE);
        return 0;
    }
    vrf_row = vrf_lookup_on_table_id(idl, table_id);
    if (vrf_row != NULL)
    {
        snprintf(vrf_ns_name, UUID_LEN+1, UUID_FMT, UUID_ARGS(&(vrf_row->header_.uuid)));
        return 0;
    }

    return -1;
}

/************************************************************************//**
 * Returns the VRF UUID from a ovsdb based on table_id.
 *
 * @param[in]  idl       : idl reference to OVSDB
 * @param[in]  table_id  : VRF table_id to use to locate the VRF record
 * @param[in,out]  uuid  : UUID structure to be filled from VRF.
 *
 * @return UUID if sucessful, else NULL on failure
 ***************************************************************************/
const int64_t
get_vrf_uuid_from_table_id (const struct ovsdb_idl *idl, const int64_t table_id,
                            struct uuid *uuid)
{
    const struct ovsrec_vrf *vrf_row = NULL;

    if (uuid == NULL)
       return -1;

    vrf_row = vrf_lookup_on_table_id(idl, table_id);
    if (vrf_row != NULL)
    {
        *uuid = vrf_row->header_.uuid;
        return 0;
    }

    return -1;
}

/************************************************************************//**
 * Returns the VRF table_id from a ovsdb based on UUID.
 *
 * @param[in]  idl   : idl reference to OVSDB
 * @param[in]  uuid  : VRF UUID to use to locate the VRF record
 *
 * @return table_id if sucessful, else negative value on failure
 ***************************************************************************/
const int64_t
get_vrf_table_id_from_uuid (const struct ovsdb_idl *idl, const struct uuid *uuid)
{
    const struct ovsrec_vrf *vrf_row = NULL;

    if (uuid == NULL)
       return -1;

    vrf_row = ovsrec_vrf_get_for_uuid(idl, uuid);
    if(vrf_row != NULL)
        return *vrf_row->table_id;

    return -1;
}

/************************************************************************//**
 * Returns the VRF UUID from a ovsdb based on vrf name.
 *
 * @param[in]  idl       : idl reference to OVSDB
 * @param[in]  vrf_name  : VRF namespace to use to locate the VRF record
 * @param[in,out]  uuid  : UUID structure to be filled from VRF.
 *
 * @return 0 if sucessful, else negetive on failure
**************************************************************************/
const int64_t
get_vrf_uuid_from_vrf_name (const struct ovsdb_idl *idl, const char *vrf_name,
                            struct uuid *uuid)
{
    const struct ovsrec_vrf *vrf_row = NULL;

    if (uuid == NULL)
       return -1;

    vrf_row = vrf_lookup(idl, vrf_name);
    if (vrf_row != NULL)
    {
        *uuid = vrf_row->header_.uuid;
        return 0;
    }
    return -1;
}

/************************************************************************//**
 * Returns the VRF name from a ovsdb based on uuid.
 *
 * @param[in]  idl   : idl reference to OVSDB
 * @param[in]  uuid  : UUID structure to be used for lookup.
 *
 * @return name if sucessful, else NULL on failure
**************************************************************************/
const char *
get_vrf_name_from_uuid (const struct ovsdb_idl *idl, const struct uuid *uuid)
{
    const struct ovsrec_vrf *vrf_row = NULL;

    if (uuid == NULL)
       return NULL;

    vrf_row = ovsrec_vrf_get_for_uuid(idl, uuid);
    if(vrf_row != NULL)
        return vrf_row->name;

    return NULL;
}

/***************************************************************************
* thread routine to enter the namespace and execute the given task.
*
* @param[in]  arg : struct nlutils_op_data parameter for parsing
*
* executes desired operation and stores the result in arg itself
***************************************************************************/
static void *vrfThread (void *arg)
{
   struct nlutils_op_data *tdata=(struct nlutils_op_data *)arg;

   if (nl_setns_with_name(tdata->ns_name) != 0)
   {
	   _exit(EXIT_SUCCESS);
   }
   nl_perform_socket_operation(tdata);
   pthread_exit(NULL);
}

/***************************************************************************
* Helper routine to enter the invoke vrf thread for the given task.
*
* @param[in]  tdata : struct nlutils_op_data parameter for parsing
*
* executes desired operation and returns true/false
***************************************************************************/
static bool vrf_perform_socket_operation (struct nlutils_op_data *tdata)
{
    int err_no;
    pthread_t tid;

    if (!(err_no = pthread_create(&tid, NULL, vrfThread, (void *)tdata))) {
        pthread_join(tid, NULL);
    } else {
        VLOG_ERR("thread create failed with error code %d", err_no);
        return false;
    }
    return true;
}
/***************************************************************************
* creates an socket by entering the corresponding namespace by spawning the
* thread.
*
* @param[in]  vrf_ns_name : this is the namespace in which socket to be opened.
* @param[in]  socket_fd : fd of the socket to close.
*
* @return valid true if sucessful, else false on failure
******************************************************************************/
int  vrf_create_socket (char* vrf_ns_name, struct vrf_sock_params *params)
{
    struct nlutils_op_data tdata;

    snprintf(tdata.ns_name, MAX_BUFFER_SIZE-1, "%s", vrf_ns_name);
    tdata.operation = NLUTILS_SOCKET_CREATE;
    tdata.params.s = &params->nl_params;
    if (is_nondefault_vrf(vrf_ns_name))
    {
        vrf_perform_socket_operation(&tdata);
    } else {
        nl_perform_socket_operation(&tdata);
    }

    return tdata.result;
}


/***************************************************************************
 * Creates a socket by entering the corresponding namespace
 *
 * @param[in]  idl       : idl reference to OVSDB
 * @param[in]  table_id  : table_id of the VRF namespace in which the socket
 *                         needs to be opened.
 * @param[in]  params    : contains socket params to pass to the socket.
 *
 * @return valid fd if sucessful, else 0 on failure
***************************************************************************/

int vrf_create_socket_using_table_id (const struct ovsdb_idl *idl, int64_t table_id,
                                      struct vrf_sock_params *params)
{
    char vrf_ns_name[UUID_LEN+1] = {0};

    if (get_vrf_ns_from_table_id(idl, table_id, vrf_ns_name) == 0)
    {
        return vrf_create_socket(vrf_ns_name, params);
    }

    return -1;
}

/***************************************************************************
 * Closes a socket by entering the corresponding namespace
 *
 * @param[in]  idl       : idl reference to OVSDB
 * @param[in]  table_id  : table_id of the VRF namespace in which the socket
 *                         needs to be closed.
 * @param[in]  socket_fd : fd of the socket that need to be closed.
 *
 * @return 0 if sucessful, else negative value on failure
 ***************************************************************************/
int vrf_close_socket_using_table_id (const struct ovsdb_idl *idl,
                                     int64_t table_id, int socket_fd)
{
    const struct ovsrec_vrf *vrf_row = NULL;

    vrf_row = vrf_lookup_on_table_id(idl, table_id);
    if (vrf_row != NULL)
    {
        if (nl_close_ns_socket(vrf_row->name, socket_fd))
            return 0;
    }
    return -1;
}

/***************************************************************************
 * check if the vrf_name is default vrf or not.
 *
 * @param[in]  vrf_name  : the namespace name corresponding to given vrf.
 *
 * @return 0 if default vrf, else 1
 ***************************************************************************/
bool is_nondefault_vrf(const char *vrf_name)
{
     if (!vrf_name  || strncmp(vrf_name, SWITCH_NAMESPACE, strlen(SWITCH_NAMESPACE)) == 0
         || strncmp(vrf_name, DEFAULT_VRF_NAME, strlen(DEFAULT_VRF_NAME)) == 0)
     {
        /* DEFAULT namespace. ignore entering this namespace again */
        return 0;
     }
     return 1;
}

/***************************************************************************
 * enters a namespace with the given vrf name
 *
 * @param[in]  vrf_name  : the namespace name corresponding to vrf.
 *
 * @return 0 if sucessful, else negative value on failure
 ***************************************************************************/
int vrf_setns_with_name (const struct ovsdb_idl *idl, const char *vrf_name)
{
    char vrf_ns_name[UUID_LEN+1] = {0};
    if (get_vrf_ns_from_name(idl, vrf_name, vrf_ns_name) == 0)
        return nl_setns_with_name(vrf_ns_name);

    return -1;
}

/***************************************************************************
 * enters a namespace with the given vrf table_id
 *
 * @param[in]  idl  : the ovsdb_idl structure corresponding to vrf
 * @param[in]  table_id  : table_id of the VRF to use for conversion
 *
 * @return 0 if sucessful, else negative value on failure
 ***************************************************************************/
int vrf_setns_with_table_id (const struct ovsdb_idl *idl, int64_t table_id)
{
    int fd = -1;
    char ns_path[MAX_BUFFER_SIZE] = {0};
    char vrf_ns_name[UUID_LEN+1] = {0};

    if (!table_id)
    {
       /* SWITCH Namespace id will always be zero. avoid
        * entering this namespace, as it is parent
        */
       return 0;
    }

    if (get_vrf_ns_from_table_id(idl, table_id, vrf_ns_name) != 0)
    {
        VLOG_ERR("Unable to find namespace for table_id %ld",
                (long int)table_id);
        return -1;
    }
    strcat(ns_path, "/var/run/netns/");
    snprintf(ns_path+strlen(ns_path), strlen(vrf_ns_name), "%s", vrf_ns_name);
    fd = open(ns_path, O_RDONLY);  /* Get descriptor for namespace */
    if (fd == -1)
    {
        VLOG_ERR("%s: namespace does not exist\n", vrf_ns_name);
        return -1;
    }

    if (setns(fd, CLONE_NEWNET) == -1) /* Join that namespace */
    {
        VLOG_ERR("Unable to set namespace to the thread errno %d", errno);
        close(fd);
        return -1;
    }

    close(fd);
    return 0;
}

/***************************************************************************
* Retrieves the if index from the ifname in given namespace
*
* @param[in]  idl  : the ovsdb_idl structure corresponding to vrf
* @param[in]  if_name : for which the ifindex to be retrieved.
* @param[in]  vrf_name : this is the vrf name in which search to be performed.
*
* @return valid ifindex if sucessful, else 0 on failure
***************************************************************************/
unsigned int vrf_if_nametoindex (const struct ovsdb_idl *idl,
                                 const char *vrf_name, const char* if_name)
{
    unsigned int ifindex = 0;
    struct nlutils_op_data tdata;
    char vrf_ns_name[UUID_LEN+1] = {0};

    if (get_vrf_ns_from_name(idl, vrf_name, vrf_ns_name) != 0) {
        VLOG_ERR("Unable to find namespace for vrf name %s", vrf_name);
        return -1;
    }
    snprintf(tdata.ns_name, MAX_BUFFER_SIZE-1, "%s", vrf_ns_name);
    snprintf(tdata.params.ni.ifname, IFNAMSIZ-1, "%s", if_name);
    tdata.operation = NLUTILS_IFNAME_TO_INDEX;
    if (is_nondefault_vrf(vrf_ns_name))
    {
        vrf_perform_socket_operation(&tdata);
    } else {
        nl_perform_socket_operation(&tdata);
    }
    ifindex = tdata.params.ni.ifindex;

    return ifindex;
}

/***************************************************************************
* Retrieves the if name from the ifindex in given namespace
*
* @param[in]  idl  : the ovsdb_idl structure corresponding to vrf
* @param[in]  ifindex : ifindex for which the ifname to be retrieved.
* @param[in]  vrf_name : this is the vrf name in which search to be performed.
*
* @param[out]  if_name : this is the ifname corresponding to the ifindex.
* @return 0 if sucessful, else -1 on failure
***************************************************************************/
unsigned int
vrf_if_indextoname (const struct ovsdb_idl *idl, const int ifindex,
                    char *if_name, const char *vrf_name)
{
    struct nlutils_op_data tdata;
    char vrf_ns_name[UUID_LEN+1] = {0};

    if (get_vrf_ns_from_name(idl, vrf_name, vrf_ns_name) != 0) {
        VLOG_ERR("Unable to find namespace for vrf name %s", vrf_name);
        return -1;
    }
    snprintf(tdata.ns_name, MAX_BUFFER_SIZE-1, "%s", vrf_ns_name);
    tdata.params.in.ifindex = ifindex;
    tdata.operation = NLUTILS_IFINDEX_TO_NAME;
    if (is_nondefault_vrf(vrf_ns_name))
    {
        vrf_perform_socket_operation(&tdata);
    } else {
        nl_perform_socket_operation(&tdata);
    }
    snprintf(if_name, IFNAMSIZ-1, "%s", tdata.params.in.ifname);

    return 0;
}

/***************************************************************************
 * Verifies if the VRF namespace / device is configuration ready
 *
 * @param[in]  idl  : the ovsdb_idl structure corresponding to vrf
 * @param[in]  vrf_name : this is the namespace in which search to be performed.
 *
 * @return true if ready, else false.
 ***************************************************************************/
bool
vrf_is_ready (const struct ovsdb_idl *idl, char *vrf_name)
{
    if (!is_nondefault_vrf(vrf_name))
    {
        return true;
    }
    const struct ovsrec_vrf *vrf = vrf_lookup(idl, vrf_name);
    if (vrf && smap_get(&vrf->status, VRF_STATUS_KEY) &&
        !strncmp(smap_get(&vrf->status, VRF_STATUS_KEY), VRF_STATUS_VALUE,
                                                   strlen(VRF_STATUS_VALUE) + 1))
    {
        return true;
    }
    return false;
}
