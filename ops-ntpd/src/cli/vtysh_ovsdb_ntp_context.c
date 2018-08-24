/* NTP daemon client callback registration source files.
 *
 * Copyright (C) 2016 Hewlett Packard Enterprise Development LP.
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation; either version 2, or (at your option) any
 * later version.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
 * MA 02110-1301, USA.
 *
 * File: vtysh_ovsdb_ntp_context.c
 *
 * Purpose: Source for registering sub-context callback with
 *          global config context.
 */

#include "vtysh/vty.h"
#include "vtysh/vector.h"
#include "vswitch-idl.h"
#include "openswitch-idl.h"
#include "vtysh/vtysh_ovsdb_if.h"
#include "vtysh/vtysh_ovsdb_config.h"
#include "vtysh/utils/system_vtysh_utils.h"
#include "vtysh_ovsdb_ntp_context.h"


/*-----------------------------------------------------------------------------
| Function : vtysh_config_context_ntp_clientcallback
| Responsibility : NTP config client callback routine
| Parameters :
|     void *p_private: void type object typecast to required
| Return : error/ok
-----------------------------------------------------------------------------*/
vtysh_ret_val
vtysh_config_context_ntp_clientcallback(void *p_private)
{
    vtysh_ovsdb_cbmsg_ptr p_msg = (vtysh_ovsdb_cbmsg *)p_private;
    const char *buf = NULL;
    const struct ovsrec_ntp_key *ntp_auth_key_row = NULL;
    const struct ovsrec_ntp_association *ntp_assoc_row = NULL;
    char str_temp[80] = "";
    bool status = false;

    vtysh_ovsdb_config_logmsg(VTYSH_OVSDB_CONFIG_DBG,
                              "vtysh_config_context_ntp_clientcallback entered");

    /* Generate CLI for the NTP_Key Table */
    OVSREC_NTP_KEY_FOR_EACH(ntp_auth_key_row, p_msg->idl) {
        vtysh_ovsdb_cli_print(p_msg, "ntp authentication-key %d md5 %s", ntp_auth_key_row->key_id, ntp_auth_key_row->key_password);

        if (ntp_auth_key_row->trust_enable) {
            vtysh_ovsdb_cli_print(p_msg, "ntp trusted-key %d", ntp_auth_key_row->key_id);
        }
    }

    /* Generate CLI for the NTP_Association Table */
    OVSREC_NTP_ASSOCIATION_FOR_EACH(ntp_assoc_row, p_msg->idl) {
        memset(str_temp, 0, sizeof(str_temp));
        if (NULL != ntp_assoc_row->key_id) {
            snprintf(str_temp, sizeof(str_temp), " key-id %ld", ((struct ovsrec_ntp_key *)ntp_assoc_row->key_id)->key_id);
        }

        buf = smap_get(&ntp_assoc_row->association_attributes, NTP_ASSOC_ATTRIB_VERSION);
        if (buf && (0 != strncmp(buf, NTP_ASSOC_ATTRIB_VERSION_DEFAULT, strlen(NTP_ASSOC_ATTRIB_VERSION_DEFAULT)))) {
            strcat(str_temp, " version ");
            strcat(str_temp, buf);
        }

        status = smap_get_bool(&ntp_assoc_row->association_attributes, NTP_ASSOC_ATTRIB_PREFER, false);
        if (status != NTP_ASSOC_ATTRIB_PREFER_DEFAULT_VAL) {
            strcat(str_temp, " prefer");
        }

        vtysh_ovsdb_cli_print(p_msg, "ntp server %s%s", ntp_assoc_row->address, str_temp);
    }

    return e_vtysh_ok;
}
