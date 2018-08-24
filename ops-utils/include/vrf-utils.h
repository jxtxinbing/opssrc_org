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
 * @defgroup vrf_utils Core Utilities
 * This library provides common utility functions used by various OpenSwitch
 * processes.
 * @{
 *
 * @defgroup vrf_utils_public Public Interface
 * Public API for vrf_utils library.
 *
 * - Math: A set of functions that do conversion from one format to another.
 * - PID: A set of functions used to record and read dameon process id.
 *
 * @{
 *
 * @file
 * Header for vrf_utils library.
 ***************************************************************************/

#ifndef __VRF_UTILS_H_
#define __VRF_UTILS_H_

#include "vswitch-idl.h"
#include "nl-utils.h"

#define VRF_STATUS_KEY   "namespace_ready"
#define VRF_STATUS_VALUE "true"
struct vrf_sock_params
{
    struct nl_sock_params nl_params;
};

/************************************************************************//**
 * Reads the vrf row from a ovsdb based on vrf name.
 *
 * @param[in]  vrf_name  :VRF name to use to locate the record
 * @param[in]  idl       : idl reference to OVSDB
 *
 * @return row if sucessful, else NULL on failure
 ***************************************************************************/
extern const struct ovsrec_vrf *
vrf_lookup(const struct ovsdb_idl *idl, const char *vrf_name);

/************************************************************************//**
 * Returns the default vrf row from a ovsdb.
 *
 * @param[in]  idl       : idl reference to OVSDB
 *
 * @return row if sucessful, else NULL on failure
 ***************************************************************************/
extern const struct ovsrec_vrf *
get_default_vrf(const struct ovsdb_idl *idl);

/************************************************************************//**
 * Returns the vrf row from a ovsdb based on vrf table_id.
 *
 * @param[in]  idl       : idl reference to OVSDB
 * @param[in]  table_id  : VRF table_id to use to locate the record
 *
 * @return row if sucessful, else NULL on failure
 ***************************************************************************/
extern const struct ovsrec_vrf *
vrf_lookup_on_table_id(const struct ovsdb_idl *idl, const int64_t table_id);

/************************************************************************//**
 * Returns the VRF UUID from a ovsdb based on table_id.
 *
 * @param[in]  idl       : idl reference to OVSDB
 * @param[in]  table_id  : VRF table_id to use to locate the VRF record
 * @param[in,out]  uuid  : UUID structure to be filled from VRF.
 *
 * @return UUID if sucessful, else NULL on failure
 ***************************************************************************/
extern const int64_t
get_vrf_uuid_from_table_id (const struct ovsdb_idl *idl, const int64_t table_id,
                            struct uuid *uuid);

/************************************************************************//**
 * Returns the VRF table_id from a ovsdb based on UUID.
 *
 * @param[in]  idl   : idl reference to OVSDB
 * @param[in]  uuid  : VRF UUID to use to locate the VRF record
 *
 * @return table_id if sucessful, else negative value on failure
 ***************************************************************************/
extern const int64_t
get_vrf_table_id_from_uuid(const struct ovsdb_idl *idl, const struct uuid *uuid);

/***************************************************************************
 * Creates a socket by entering the corresponding namespace using id
 *
 * @param[in]  idl       : idl reference to OVSDB
 * @param[in]  table_id  : table_id of the VRF namespace in which the socket
 *                         needs to be opened.
 * @param[in]  params    : contains socket params to pass to the socket.
 *
 * @return valid fd if sucessful, else 0 on failure
 ***************************************************************************/
extern int vrf_create_socket_using_table_id(const struct ovsdb_idl *idl,
                                            int64_t table_id,
                                            struct vrf_sock_params *params);

/***************************************************************************
 * Closes a socket by entering the corresponding namespace using id
 *
 * @param[in]  idl       : idl reference to OVSDB
 * @param[in]  table_id  : table_id of the VRF namespace in which the socket
 *                         needs to be closed.
 * @param[in]  socket_fd : fd of the socket that need to be closed.
 *
 * @return 0 if sucessful, else negative value on failure
 ***************************************************************************/
extern int
vrf_close_socket_using_table_id (const struct ovsdb_idl *idl, int64_t table_id,
                                 int socket_fd);

/***************************************************************************
 * enters a namespace with the given vrf name
 *
 * @param[in]  idl  : the ovsdb_idl structure corresponding to vrf
 * @param[in]  vrf_name  : the namespace name corresponding to given vrf.
 *
 * @return 0 if sucessful, else negative value on failure
 ***************************************************************************/
int vrf_setns_with_name(const struct ovsdb_idl *idl, const char *vrf_name);

/***************************************************************************
 * enters a namespace with the given vrf table_id
 *
 * @param[in]  idl  : the ovsdb_idl structure corresponding to vrf
 * @param[in]  table_id  : table_id of the VRF to use for conversion
 *
 * @return 0 if sucessful, else negative value on failure
 ***************************************************************************/
int vrf_setns_with_table_id(const struct ovsdb_idl *idl, int64_t table_id);

/***************************************************************************
 * returns if the passed vrf name matches with default namespace or not.
 *
 * @param[in]  vrf_ns_name  : the namespace name passed
 *
 * @return 0 if if default vrf. else 1 if passed name is not a vrf.
 ***************************************************************************/
bool is_nondefault_vrf(const char *vrf_ns_name);

/***************************************************************************
* creates an socket by entering the corresponding namespace by spawning the
* thread.
*
* @param[in]  vrf_ns_name : this is the namespace in which socket to be opened.
* @param[in]  socket_fd : fd of the socket to close.
*
* @return valid true if sucessful, else false on failure
***************************************************************************/
int  vrf_create_socket (char* vrf_ns_name, struct vrf_sock_params *params);

/***************************************************************************
 * Verifies if the VRF namespace / device is configuration ready
 *
 * @param[in]  idl  : the ovsdb_idl structure corresponding to vrf
 * @param[in]  vrf_name : this is the namespace in which search to be performed.
 *
 * @return true if ready, else false.
 ***************************************************************************/
bool
vrf_is_ready(const struct ovsdb_idl *idl, char *vrf_name);

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
get_vrf_ns_from_name(const struct ovsdb_idl *idl, const char* vrf_name,
                     char* vrf_ns_name);
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
get_vrf_ns_from_table_id(const struct ovsdb_idl *idl, const int64_t table_id,
                         char* vrf_ns_name);

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
get_vrf_uuid_from_table_id(const struct ovsdb_idl *idl, const int64_t table_id,
                           struct uuid *uuid);
#endif /* __VRF_UTILS_H_ */
/** @} end of group vrf_utils_public */
/** @} end of group vrf_utils */
