/* OSPFd debug CLI header file
 *
 * Copyright (C) 2016 Hewlett Packard Enterprise Development LP
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * File: ospf_debug_vty.h
 *
 * Purpose: header file for ospf_debug_vty.c
 */

#ifndef __ZLOG_LIST_VTY_H
#define __ZLOG_LIST_VTY_H

#include "vtysh/command.h"
#include "vtysh/vtysh.h"
#include "vtysh/vtysh_user.h"
#include "vtysh/memory.h"
#include "dirs.h"
#include "util.h"
#include "daemon.h"
#include "unixctl.h"
#include "dynamic-string.h"

#define DBG_CMD_LEN_MAX    50

#define  ERR_STR\
    "Error in retrieving the mapping of feature names to daemon names"
#define DBG_STR            "Debug Configuration\n"
#define SHOW_DBG_STR       "Debugging Configuration\n"
#define OSPF_STR           "OSPF information\n"
#define OSPFv2_STR           "OSPFv2 information\n"
#define OSPFv2_PACKETS       "OSPFv2 packets\n"
#define OSPFv2_HELLO         "OSPFv2 Hello\n"
#define OSPFv2_DB_DESC       "OSPFv2 Database Description\n"
#define OSPFv2_LINK_STATE_REQ "OSPFv2 Link State Request\n"
#define OSPFv2_LINK_STATE_UPD "OSPFv2 Link State Update\n"
#define OSPFv2_Link_STATE_ACK "OSPFv2 Link State Acknowledgment\n"
#define OSPFv2_All_PACKETS    "OSPFv2 all packets\n"
#define OSPFv2_PACKET_SENT    "Packets sent\n"
#define OSPFv2_PACKET_RECV    "Packets received\n"
#define OSPFv2_DETAIL_INFO    "Detail information\n"
#define OSPFv2_ISM            "OSPFv2 Interface State Machine\n"
#define OSPFv2_ISM_STAT_INFO  "ISM Status Information\n"
#define OSPFv2_ISM_EVT_INFO   "ISM Event Information\n"
#define OSPFv2_ISM_TIMER_INFO "ISM TImer Information\n"
#define OSPFv2_NSM            "OSPFv2 Neighbor State Machine\n"
#define OSPFv2_NSM_STAT_INFO  "NSM Status Information\n"
#define OSPFv2_NSM_EVT_INFO   "NSM Event Information\n"
#define OSPFv2_NSM_TIMER_INFO "NSM Timer Information\n"
#define OSPFv2_LSA            "OSPFv2 Link State Advertisement\n"
#define OSPFv2_LSA_GEN        "LSA Generation\n"
#define OSPFv2_LSA_FLOOD      "LSA Flooding\n"
#define OSPFv2_LSA_INST       "LSA Install/Delete\n"
#define OSPFv2_LSA_REF        "LSA Refresh\n"
#define OSPFv2_EVT_INFO       "OSPFv2 event information\n"
#define OSPFv2_NSSA_INFO      "OSPFv2 NSSA information\n"
#define OSPFv2_INTF_INFO      "OSPFv2 interface information\n"
#define OSPFv2_REDIST_INFO    "OSPFv2 redistribute information\n"

#endif /*__ZLOG_LIST_VTY_H*/
