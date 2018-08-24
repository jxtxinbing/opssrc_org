/*
 Copyright (C) 2015 Hewlett-Packard Development Company, L.P.
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
 * @defgroup ops_utils Core Utilities
 * This library provides common utility functions used by various OpenSwitch
 * processes.
 * @{
 *
 * @defgroup ops_utils_public Public Interface
 * Public API for ops_utils library.
 *
 * - Math: A set of functions that do conversion from one format to another.
 * - PID: A set of functions used to record and read dameon process id.
 *
 * @{
 *
 * @file
 * Header for ops_utils library.
 ***************************************************************************/

#ifndef __OPS_UTILS_H_
#define __OPS_UTILS_H_

#include <netinet/ether.h>
#include "shash.h"
#include "vswitch-idl.h"

/******************* MATH *************************/

#define OPS_MAC_STR_SIZE	18    /*!< Number of bytes in a MAC ADDR string */
#define OPS_WWN_STR_SIZE	24    /*!< Number of bytes in a WWN string */


/************************************************************************//**
 * Converts an Ethernet address pointed to by addr to a string
 * mac_a with leading zeros.
 *
 * @param[out] mac_a :MAC address string
 * @param[in]  addr  :Ethernet address
 *
 * @return MAC address string
 ***************************************************************************/
extern char *ops_ether_ntoa(char *mac_a, const struct ether_addr *addr);

/************************************************************************//**
 * This function is a World Wide Name version of ops_ether_ntoa and converts
 * a WWN address pointed to by wwn to a string wwn_a with leading zeros.
 *
 * @param[out] wwn_a :WWN address string
 * @param[in]  wwn   :World Wide Name
 *
 * @return WWN address string
 ***************************************************************************/
extern char *ops_wwn_ntoa(char *wwn_a, const char *wwn);

/************************************************************************//**
 * Converts a generic array of binary octets into
 * unsigned long long. This can be handy for incrementing MACs or WWNs.
 *
 * @param[in]  char_array :input array with most significant byte first
 * @param[in]  length     :length of input string
 *
 * @return ull binary value of input string
 ***************************************************************************/
extern unsigned long long
    ops_char_array_to_ulong_long(unsigned char *char_array, unsigned int length);

/************************************************************************//**
 * Converts an unsigned long long into generic array of
 * binary octets. Output is array with most significant byte first
 *
 * @param[in]  value      :ull binary value
 * @param[in]  length     :number of bytes to process
 * @param[out] char_array :char array with converted bytes
 *
 * @return void
 ***************************************************************************/
extern void ops_ulong_long_to_char_array(unsigned long long value,
        unsigned int length, unsigned char *char_array);

/************************************************************************//**
 * Converts an Ethernet address stored as a 6 byte binary array
 * into a printable mac address with leading zeros.
 *
 * @param[out] mac_a    :MAC address string
 * @param[in]  addr     :6 byte binary array with MAC address
 *
 * @return MAC address string
 ***************************************************************************/
extern char *ops_ether_array_to_string(char *mac_a, const unsigned char *addr);

/************************************************************************//**
 * Converts an Ethernet address stored as a long long
 * into a printable mac address with leading zeros. returns mac_a.
 *
 * @param[out] mac_a  :MAC address string
 * @param[in]  mac    :ull MAC address
 *
 * @return MAC address string
 ***************************************************************************/
extern char *ops_ether_ulong_long_to_string(char *mac_a,
        const unsigned long long mac);


/******************* PID Utility *******************/

/************************************************************************//**
 * Writes the process id to a file.
 *
 * @param[in]  filename  :Filename to write pid
 *
 * @return zero for success, else errno on failure
 ***************************************************************************/
extern int ops_record_pid(const char *filename);

/************************************************************************//**
 * Reads a process id stored in a file.
 *
 * @param[in]  filename  :Filename with the pid
 *
 * @return PID if sucessful, else errno on failure
 ***************************************************************************/
extern int ops_read_pid(const char *filename);

/************************************************************************//**
 * Reads the PID from a file based on process name.
 *
 * @param[in]  procname  :Process name to use to locate the PID file
 *
 * @return PID if sucessful, else errno on failure
 ***************************************************************************/
extern int ops_read_pid_by_procname(const char *procname);


/******************* Sort Utility *******************/

/************************************************************************//**
 * The function is a generic quick sort algorithm
 *
 * @param[out] sorted_list  : shash node containing sorted elements. The
 *                            caller must make sure to allocate/de-allocate
 *                            memory for sorted_list
 * @param[in]  sh           : shash node containing unsorted elements
 * @param[in]  ptr_fuc_sort : pointer to function which contains the
 *                            compartor logic for sorting algorithm
 *
 * @return zero for success, else non-zero on failure
 ***************************************************************************/
int
ops_sort(const struct shash *sh, void *ptr_func_sort,
         const struct shash_node ** sorted_list);

/******************** OVSDB Utility ******************************************/

/******************************************************************************
 * Setter function for tag column of port table
 *
 * @param[in]  vlan_id  : vlan id to be set for tag column of port table
 * @param[in]  port_row : port table record for which tag has to be set
 * @param[in]  idl      : pointer to ovsdb handler
 *
 * @return true for success, else false on failure
 *****************************************************************************/
bool ops_port_set_tag(int vlan_id,
                      const struct ovsrec_port *port_row,
                      struct ovsdb_idl *idl);

/******************************************************************************
 * Setter function for trunk column of port table
 *
 * @param[in]  trunk_vlan_ids   : pointer to array conataining trunked VLANs
 * @param[in]  trunk_vlan_count : count of trunk VLANs
 * @param[in]  port_row         : port table record for which trunked VLANs
 *                                record has to be set
 * @param[in]  idl              : pointer to ovsdb handler
 *
 * @return true for success, else false on failure
 *****************************************************************************/
bool ops_port_set_trunks(int64_t *trunk_vlan_ids,
                         int trunk_vlan_count,
                         const struct ovsrec_port *port_row,
                         struct ovsdb_idl *idl);

/******************************************************************************
 * Setter function for vlan column of mac table
 *
 * @param[in]  vlan_id  : vlan id to be set for vlan column in mac table
 * @param[in]  mac_row  : mac table record for which vlan has to set
 * @param[in]  idl      : pointer to ovsdb handler
 *
 * @return true for success, else false on failure
 *****************************************************************************/
bool ops_mac_set_vlan(int64_t vlan_id,
                      const struct ovsrec_mac *mac_row,
                      struct ovsdb_idl *idl);

/******************************************************************************
 * Getter function for tag column of port table
 *
 * @param[in]  port_row : port table record for which tag has to be fetched
 * @param[in]  idl      : pointer to ovsdb handler
 *
 * @return vlan identifier
 *****************************************************************************/
int ops_port_get_tag(const struct ovsrec_port *port_row);

/******************************************************************************
 * Getter function for trunk column of port table
 *
 * @param[in]  port_row : port table record for which trunk VLAN has to be
 *                        fetched
 * @param[in]  index    : index of the trunked VLAN
 *
 * @return vlan identifier
 *****************************************************************************/
int ops_port_get_trunks(const struct ovsrec_port *port_row,
                        int index);

/******************************************************************************
 * Getter function for vlan column of mac table
 *
 * @param[in]  port_row : mac table record for which vlan has to be fetched
 *
 * @return vlan identifier
 *****************************************************************************/
int ops_mac_get_vlan(const struct ovsrec_mac *mac_row);

/******************************************************************************
 * Setter function for tag column of port table
 *
 * @param[in]  vlan_id  : vlan id to be set for tag column of port table
 *
 * @return vlan_row for the vlan_id if found, else NULL
 *****************************************************************************/
const struct ovsrec_vlan * ops_get_vlan_by_id(int vlan_id,
                                              struct ovsdb_idl *idl);

/******************** OVSDB Utility ******************************************/

/******************************************************************************
 * Setter function for tag column of port table
 *
 * @param[in]  vlan_id  : vlan id to be set for tag column of port table
 * @param[in]  port_row : port table record for which tag has to be set
 * @param[in]  idl      : pointer to ovsdb handler
 *
 * @return true for success, else false on failure
 *****************************************************************************/
bool ops_port_set_tag(int vlan_id,
                      const struct ovsrec_port *port_row,
                      struct ovsdb_idl *idl);

/******************************************************************************
 * Setter function for trunk column of port table
 *
 * @param[in]  trunk_vlan_ids   : pointer to array conataining trunked VLANs
 * @param[in]  trunk_vlan_count : count of trunk VLANs
 * @param[in]  port_row         : port table record for which trunked VLANs
 *                                record has to be set
 * @param[in]  idl              : pointer to ovsdb handler
 *
 * @return true for success, else false on failure
 *****************************************************************************/
bool ops_port_set_trunks(int64_t *trunk_vlan_ids,
                         int trunk_vlan_count,
                         const struct ovsrec_port *port_row,
                         struct ovsdb_idl *idl);

/******************************************************************************
 * Setter function for vlan column of mac table
 *
 * @param[in]  vlan_id  : vlan id to be set for vlan column in mac table
 * @param[in]  mac_row  : mac table record for which vlan has to set
 * @param[in]  idl      : pointer to ovsdb handler
 *
 * @return true for success, else false on failure
 *****************************************************************************/
bool ops_mac_set_vlan(int64_t vlan_id,
                      const struct ovsrec_mac *mac_row,
                      struct ovsdb_idl *idl);

/******************************************************************************
 * Getter function for tag column of port table
 *
 * @param[in]  port_row : port table record for which tag has to be fetched
 * @param[in]  idl      : pointer to ovsdb handler
 *
 * @return vlan identifier
 *****************************************************************************/
int ops_port_get_tag(const struct ovsrec_port *port_row);

/******************************************************************************
 * Getter function for trunk column of port table
 *
 * @param[in]  port_row : port table record for which trunk VLAN has to be
 *                        fetched
 * @param[in]  index    : index of the trunked VLAN
 *
 * @return vlan identifier
 *****************************************************************************/
int ops_port_get_trunks(const struct ovsrec_port *port_row,
                        int index);

/******************************************************************************
 * Getter function for vlan column of mac table
 *
 * @param[in]  port_row : mac table record for which vlan has to be fetched
 *
 * @return vlan identifier
 *****************************************************************************/
int ops_mac_get_vlan(const struct ovsrec_mac *mac_row);

/******************************************************************************
 * Setter function for tag column of port table
 *
 * @param[in]  vlan_id  : vlan id to be set for tag column of port table
 *
 * @return vlan_row for the vlan_id if found, else NULL
 *****************************************************************************/
const struct ovsrec_vlan * ops_get_vlan_by_id(int vlan_id,
                                              struct ovsdb_idl *idl);

/*****************************************************************************
sends a ICMP_ECHO packet to the target.
 @param[in] target: ipv4 address string of the target to ping
 @return void
******************************************************************************/
extern int ping4(const char *target);

/*****************************************************************************
sends a ICMP6_ECHO_REQUEST packet to the target.
 @param[in] target: ipv6 address string of the target to ping
 @return void
******************************************************************************/
extern int ping6(const char *target);
#endif /* __OPS_UTILS_H_ */
/** @} end of group ops_utils_public */
/** @} end of group ops_utils */
