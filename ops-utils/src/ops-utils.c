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

/*************************************************************************//**
 * @ingroup ops_utils
 * This module contains the DEFINES and functions that comprise the ops-utils
 * library.
 *
 * @file
 * Source file for ops-utils library.
 *
 ****************************************************************************/

#include <stdio.h>
#include <unistd.h>
#include <sched.h>
#include <string.h>
#include <errno.h>

#include "ops-utils.h"

/*********************************************************
 *                      PID Utility                      *
 *********************************************************/

int
ops_record_pid(const char *filename)
{
	FILE *pid_file;

	pid_file = fopen(filename, "w");
	if ((FILE *)NULL == pid_file) {
		return errno;
	}

	fprintf(pid_file, "%d\n", getpid());
	fclose(pid_file);

	return 0;

} /* ops_record_pid */

int
ops_read_pid(const char *filename)
{
	FILE *pid_file;
	int pid;

	pid_file = fopen(filename, "r");
	if ((FILE *)NULL == pid_file) {
		return -errno;
	}

	if (1 != fscanf(pid_file,"%d", &pid)) {
		pid = -EINVAL;
	}
	fclose(pid_file);

	return pid;

} /* ops_read_pid */

int
ops_read_pid_by_procname(const char *procname)
{
	char filename[80];

	snprintf(filename,sizeof(filename),"/var/run/%s.pid", procname);

	return ops_read_pid(filename);

} /* ops_read_pid_by_procname */


/*********************************************************
 *                       MATH                            *
 *********************************************************/

/*
 * ops_char_array_to_ulong_long
 *
 * Converts a generic array of binary values into unsigned long long.
 * This can be handy for incrementing MACs or WWNs.
 * Input is array with most significant byte first
 */
unsigned long long
ops_char_array_to_ulong_long(unsigned char *char_array, unsigned int length)
{
	unsigned long long   value = (unsigned long long)0;
	unsigned int    i;

	for ( i = 0; i < length; i++ ) {
		value = ( value << 8 ) + char_array[i];
	}

	return value;
} /* ops_char_array_to_ulong_long */

/*
 * ops_ulong_long_to_char_array
 *
 * Converts an unsigned long long into generic array of binary values.
 * Output is array with most significant byte first
 */
void
ops_ulong_long_to_char_array(unsigned long long value, unsigned int length,
		unsigned char *char_array)
{
	unsigned long long   temp = value;
	int     i;

	for ( i = length - 1; i >= 0; i-- ) {
		char_array[i] = temp & 0xff;
		temp >>= 8;
	}
} /* ops_ulong_long_to_char_array */

/*
 * ops_ether_ntoa - the pretty version of ether_ntoa
 *
 * converts an Ethernet address pointed to by addr to a string mac_a
 * with leading zeros. returns mac_a.
 *
 */
char *
ops_ether_ntoa(char *mac_a, const struct ether_addr *addr)
{
	(void)snprintf(mac_a, OPS_MAC_STR_SIZE, "%02x:%02x:%02x:%02x:%02x:%02x",
			addr->ether_addr_octet[0], addr->ether_addr_octet[1],
			addr->ether_addr_octet[2], addr->ether_addr_octet[3],
			addr->ether_addr_octet[4], addr->ether_addr_octet[5]);
	return mac_a;
} /* ops_ether_ntoa */

/*
 * ops_wwn_ntoa - World Wide Name version of ops_ether_ntoa
 *
 * converts a WWN address pointed to by wwn to a string wwn_a
 * with leading zeros. returns wwn_a
 */
char *
ops_wwn_ntoa(char *wwn_a, const char *wwn)
{
	(void)snprintf(wwn_a, OPS_WWN_STR_SIZE, "%02x:%02x:%02x:%02x:%02x:%02x:%02x:%02x",
			wwn[0], wwn[1], wwn[2], wwn[3], wwn[4], wwn[5], wwn[6], wwn[7]);
	return wwn_a;
} /* ops_wwn_ntoa */

/*
 * ops_ether_array_to_string
 *
 * converts an Ethernet address stored as a 6 byte binary array
 * into a printable mac address with leading zeros. returns mac_a.
 *
 */
char *
ops_ether_array_to_string(char *mac_a, const unsigned char *addr)
{
	(void)snprintf(mac_a, OPS_MAC_STR_SIZE, "%02x:%02x:%02x:%02x:%02x:%02x",
			addr[0], addr[1], addr[2], addr[3], addr[4], addr[5]);
	return mac_a;
} /* ops_ether_array_to_string */

/*
 * ops_ether_ulong_long_to_string
 *
 * converts an Ethernet address stored as a long long
 * into a printable mac address with leading zeros. returns mac_a.
 *
 */
char *
ops_ether_ulong_long_to_string(char *mac_a, const unsigned long long mac)
{
	unsigned char addr[6];
	unsigned long long max_mac = 0xffffffffffff;

	if (mac > max_mac) {
		return ( (char *) NULL);
	}
	ops_ulong_long_to_char_array(mac, ETH_ALEN, addr);

	(void)snprintf(mac_a, OPS_MAC_STR_SIZE,
		       "%02x:%02x:%02x:%02x:%02x:%02x",
		       addr[0], addr[1], addr[2], addr[3], addr[4], addr[5]);

	return mac_a;
} /* ops_ether_ulong_long_to_string */

/*
 * Sorting function for generic elemnts
 * on success, returns sorted elemnts list.
 */
int
ops_sort(const struct shash *sh, void *ptr_func_sort,
         const struct shash_node ** sorted_list)

{
    int ret_val = 0;

    if (ptr_func_sort == NULL || sorted_list == NULL || shash_is_empty(sh)) {
        ret_val = 1;
    } else {
        struct shash_node *node;

        size_t i, n;

        n = shash_count(sh);
        i = 0;
        SHASH_FOR_EACH (node, sh) {
            sorted_list[i++] = node;
        }
        ovs_assert(i == n);

        qsort(sorted_list, n, sizeof *sorted_list, ptr_func_sort);
    }
    return ret_val;
}

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
                      struct ovsdb_idl *idl)
{
    const struct ovsrec_vlan *vlan_row = NULL;
    bool ret_val = false;

    if ((port_row != NULL ) && (idl != NULL)) {
        if (vlan_id) {
            vlan_row = (const struct ovsrec_vlan *)
                        ops_get_vlan_by_id(vlan_id, idl);
            if(vlan_row != NULL) {
                ret_val = true;
            }
        }
        else {
            ret_val = true;
        }

        if(ret_val) {
            ovsrec_port_set_vlan_tag(port_row, vlan_row);
        }
    }

    return ret_val;
}

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
                         struct ovsdb_idl *idl)
{
    const struct ovsrec_vlan *vlan_row = NULL;
    struct ovsrec_vlan **vlan_trunks = NULL;
    bool ret_val = false;
    int index;

    if ((port_row != NULL) && (idl != NULL)) {
        vlan_trunks = xmalloc(sizeof(struct ovsrec_vlan *)*trunk_vlan_count);
        if(vlan_trunks != NULL) {
            for (index = 0; index < trunk_vlan_count; index++) {
                vlan_row = (const struct ovsrec_vlan *)
                            ops_get_vlan_by_id(trunk_vlan_ids[index], idl);
                if(vlan_row != NULL) {
                    vlan_trunks[index] = (struct ovsrec_vlan *)vlan_row;
                    ret_val = true;
                }
                else {
                    ret_val = false;
                    break;
                }
            }

            if(trunk_vlan_count == 0) {
                ret_val = true;
            }

            if(ret_val == true) {
                ovsrec_port_set_vlan_trunks(port_row, vlan_trunks,
                                            (size_t)trunk_vlan_count);
            }

            free(vlan_trunks);
            vlan_trunks = NULL;
        }
    }

    return ret_val;
}

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
                      struct ovsdb_idl *idl)
{
    const struct ovsrec_vlan *vlan_row = NULL;
    bool ret_val = false;

    if ((mac_row != NULL) && (idl != NULL)) {
        if (vlan_id) {
            vlan_row = (const struct ovsrec_vlan *)
                        ops_get_vlan_by_id(vlan_id, idl);
            if(vlan_row != NULL) {
                ret_val = true;
            }
        }
        else {
            ret_val = true;
        }

        if(ret_val) {
            ovsrec_mac_set_mac_vlan(mac_row, vlan_row);
        }
    }

    return ret_val;
}

/******************************************************************************
 * Getter function for tag column of port table
 *
 * @param[in]  port_row : port table record for which tag has to be fetched
 * @param[in]  idl      : pointer to ovsdb handler
 *
 * @return vlan identifier
 *****************************************************************************/
int ops_port_get_tag(const struct ovsrec_port *port_row)
{
    int vlan_id = 0;

    if (port_row != NULL) {
        if (port_row->vlan_tag != NULL) {
            vlan_id = port_row->vlan_tag->id;
        }
    }

    return vlan_id;
}

/******************************************************************************
 * Getter function for trunk column of port table
 *
 * @param[in]  port_row : port table record for which trunk VLAN has to be
 *                        fetched
 * @param[in]  index    : index of the trunked VLAN
 * @param[in]  idl      : pointer to ovsdb handler
 *
 * @return vlan identifier
 *****************************************************************************/
int ops_port_get_trunks(const struct ovsrec_port *port_row,
                        int index)
{
    int vlan_id = 0;

    if (port_row != NULL) {
        if ((index >= 0) && (index < port_row->n_vlan_trunks)) {
            if (port_row->vlan_trunks != NULL) {
                if (port_row->vlan_trunks[index] != NULL) {
                    vlan_id = port_row->vlan_trunks[index]->id;
                }
            }
        }
    }

    return vlan_id;
}

/******************************************************************************
 * Getter function for vlan column of mac table
 *
 * @param[in]  port_row : mac table record for which vlan has to be fetched
 * @param[in]  idl      : pointer to ovsdb handler
 *
 * @return vlan identifier
 *****************************************************************************/
int ops_mac_get_vlan(const struct ovsrec_mac *mac_row)
{
    int vlan_id = 0;

    if (mac_row != NULL) {
        if (mac_row->mac_vlan != NULL) {
            vlan_id = mac_row->mac_vlan->id;
        }
    }

    return vlan_id;
}

/******************************************************************************
 * Setter function for tag column of port table
 *
 * @param[in]  vlan_id  : vlan id to be set for tag column of port table
 *
 * @return vlan_row for the vlan_id if found, else NULL
 *****************************************************************************/
const struct ovsrec_vlan * ops_get_vlan_by_id(int vlan_id,
                                              struct ovsdb_idl *idl)
{
    const struct ovsrec_vlan *vlan_row = NULL;

    if(idl != NULL) {
        OVSREC_VLAN_FOR_EACH (vlan_row, idl) {
            if(vlan_id == vlan_row->id) {
                break;
            }
        }
    }

    return vlan_row;
}
