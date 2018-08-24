/* OSPFd debug CLI file
*
* Copyright (C) 1997, 98 Kunihiro Ishiguro
* Copyright (C) 2016 Hewlett Packard Enterprise Development LP
*
* GNU Zebra is free software; you can redistribute it and/or modify it
* under the terms of the GNU General Public License as published by the
* Free Software Foundation; either version 2, or (at your option) any
* later version.
*
* GNU Zebra is distributed in the hope that it will be useful, but
* WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
* General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with GNU Zebra; see the file COPYING.  If not, write to the Free
* Software Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
* 02111-1307, USA.
*
* File: ospf_debug_vty.c
*
* Purpose: Showing and changing debug for ospf.
*/


#include <stdio.h>
#include <yaml.h>
#include <sys/stat.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include "openvswitch/vlog.h"
#include "vtysh/command.h"
#include "vtysh/vtysh.h"
#include "vtysh/vtysh_user.h"
#include "vtysh/memory.h"
#include "dynamic-string.h"
#include "diag_dump_vty.h"
#include "jsonrpc.h"
#include "ospf_debug_vty.h"
#include "supportability_utils.h"
#include "unixctl.h"

#define MAX_PID               65536
#define MIN_PID               1
#define MAX_PID_LEN           5
#define MIN_PID_LEN           1

VLOG_DEFINE_THIS_MODULE (vtysh_ospf_debug);

static struct feature* feature_head;
static char initialized = 0; /* flag to check before parseing yaml file */

static int
vtysh_ospf_read_pid_file (char *pidfile);

static struct jsonrpc *
vtysh_ospf_connect_to_target(const char *target);

static int
ospf_debug(const char **argv, int argc, int flag);

/*
 * Function       : vtysh_ospf_read_pid_file
 * Responsibility : read pid file
 * Parameters     : pidfile
 * Returns        : Negative integer value on failure
 *                  Positive integer value on success
 *
 * Note : read_pidfile() API is does same thing but it opens a file in "r+"
 *        mode.read_pidfile() API will success only if user has "rw" permission.
 *        If user has "r" permission then read_pidfile() API fails.
 */

static int
vtysh_ospf_read_pid_file (char *pidfile)
{
    FILE *fp = NULL;
    int pid = 0;
    int rc = 0;
    char err_buf[MAX_CLI_STR_LEN] = {0};

    if (pidfile == NULL)
    {
        VLOG_ERR("Invalid parameter pidfile");
        return -1;
    }

    fp = fopen(pidfile,"r");
    if (fp == NULL)
    {
        strerror_r (errno,err_buf,sizeof(err_buf));
        STR_SAFE(err_buf);
        VLOG_ERR("Failed to open pidfile:%s , error:%s",pidfile,err_buf);
        return -1;
    }

    rc = fscanf(fp, "%d", &pid);
    fclose(fp);

    /*
     * valid pid range : 1 to 65536
     * digit count range of valid pid : 1 to 5
     */

    if ((( rc >= MIN_PID_LEN ) && ( rc <= MAX_PID_LEN )) &&
            (( pid >= MIN_PID ) && ( pid <= MAX_PID ))) {
        return pid;
    }
    else
    {
        VLOG_ERR("Pid value is not in range : (%d-%d), pid : %d",
                MIN_PID , MAX_PID , pid);
        return -1;
    }
}

/*
 * Function       : vtysh_ospf_connect_to_target
 * Responsibility : populates jsonrpc client structure for a daemon
 * Parameters     : target  - daemon name
 * Returns        : jsonrpc client on success
 *                  NULL on failure
 */

static struct jsonrpc *
vtysh_ospf_connect_to_target(const char *target)
{
    struct jsonrpc *client=NULL;
    char *socket_name=NULL;
    int error=0;
    char * rundir = NULL;
    char *pidfile_name = NULL;
    pid_t pid=-1;

    if (!target)
    {
        VLOG_ERR("target is null");
        return NULL;
    }

    rundir = (char*) ovs_rundir();
    if (!rundir)
    {
        VLOG_ERR("rundir is null");
        return NULL;
    }

    if (target[0] != '/')
    {
        pidfile_name = xasprintf("%s/%s.pid", rundir, target);
        if (!pidfile_name)
        {
            VLOG_ERR("pidfile_name is null");
            return NULL;
        }

        pid = vtysh_ospf_read_pid_file(pidfile_name);
        if (pid < 0)
        {
            VLOG_ERR("cannot read pidfile :%s", pidfile_name);
            free(pidfile_name);
            return NULL;
        }

        free(pidfile_name);
        socket_name = xasprintf("%s/%s.%ld.ctl", rundir, target,
                (long int) pid);
        if (!socket_name)
        {
            VLOG_ERR("socket_name is null");
            return NULL;
        }

    }
    else
    {
        socket_name = xstrdup(target);
        if (!socket_name)
        {
            VLOG_ERR("socket_name is null, target:%s", target);
            return NULL;
        }
    }

    error = unixctl_client_create(socket_name, &client);
    if (error)
    {
        VLOG_ERR("cannot connect to %s,error=%d", socket_name, error);
        free(socket_name);
        return NULL;
    }
    free(socket_name);
    return client;
}

/*
 * Function       : vtysh_set_ospf_debug
 * Responsibility : send request to target daemon using unixctl and
 *                  print result to console.
 * Parameters     : daemon
 *                : cmd_type
 *                : cmd_argc
 *                : vty
 *                : fd - file descriptor
 *                : flag
 *                  prints on vtysh the result of function call.
 * Returns        : 0 on success and nonzero on failure
 */
static int
vtysh_set_ospf_debug(char* daemon, char **cmd_type, int cmd_argc,
                struct vty *vty, int fd, int flag)
{
    struct jsonrpc *client = NULL;
    char *cmd_result = NULL, *cmd_error = NULL;
    char  ospf_cmd_str[DBG_CMD_LEN_MAX] = {0};
    int rc;

    if (!(daemon && cmd_type))
    {
        VLOG_ERR("invalid parameter daemon or command ");
        return CMD_WARNING;
    }

    client = vtysh_ospf_connect_to_target(daemon);
    if (!client)
    {
        VLOG_ERR("%s transaction error.client is null ", daemon);
        vty_out(vty,"failed to connect daemon %s %s",daemon,VTY_NEWLINE);
        return CMD_WARNING;
    }

    if (flag == 0)
    {
        strncpy(ospf_cmd_str, "ospf/debug", sizeof(ospf_cmd_str));
    }
    else if (flag == 1)
    {
        strncpy(ospf_cmd_str, "ospf/show-debug", sizeof(ospf_cmd_str));
    }
    else if (flag == 2)
    {
        strncpy(ospf_cmd_str, "ospf/no-debug", sizeof(ospf_cmd_str));
    }
    else
    {
        vty_out(vty, "Error occured.%s", VTY_NEWLINE);
        return CMD_WARNING;
    }
    STR_SAFE(ospf_cmd_str);

    rc = unixctl_client_transact(client, ospf_cmd_str, cmd_argc, cmd_type,
            &cmd_result, &cmd_error);

    if (rc)
    {
        VLOG_ERR("%s: transaction error:%s , rc = %d", daemon,
                STR_NULL_CHK(cmd_error), rc);
        jsonrpc_close(client);
        FREE(cmd_result);
        FREE(cmd_error);
        return CMD_WARNING;
    }
    else if (cmd_result != NULL)
    {
        vty_out(vty, "%s%s", cmd_result, VTY_NEWLINE);
    }

   /*
   * unixctl_client_transact() api failure case
   *  check cmd_error and rc value.
   */

    if (cmd_error)
    {
        VLOG_ERR("%s: server returned error: rc=%d, error str: %s",
                daemon, rc, cmd_error);
        jsonrpc_close(client);
        FREE(cmd_result);
        FREE(cmd_error);
        return CMD_WARNING;
    }

    jsonrpc_close(client);
    FREE(cmd_result);
    FREE(cmd_error);
    return CMD_SUCCESS;
}

DEFUN (show_debugging_info,
       show_debugging_info_cmd,
       "show debugging ospfv2",
       SHOW_STR
       SHOW_DBG_STR
       OSPF_STR)
{
    int fun_argc = argc, flag = -1;
    int fd = -1;
    int rc = 0;

    struct feature* iter = feature_head;
    struct daemon* iter_daemon = NULL;
    char *fun_argv[argc];

    fun_argv[0] = (char *)  argv[0];
    flag = 1;

    if (!initialized)
    {
        feature_head  = get_feature_mapping();
        if ( feature_head == NULL )
        {
            vty_out(vty,"%s%s", ERR_STR ,VTY_NEWLINE);
            return  CMD_WARNING ;
        }
        else
        {
            initialized = 1;
        }
    }

    /* traverse linkedlist to find node */
    for (iter = feature_head ; iter &&
               strcmp_with_nullcheck(iter->name, argv[0]); iter = iter->next);

    VLOG_DBG("feature:%s , desc:%s",STR_NULL_CHK(iter->name),
                STR_NULL_CHK(iter->desc));

    iter_daemon = iter->p_daemon;
    while(iter_daemon)
    {
        rc = vtysh_set_ospf_debug(iter_daemon->name, fun_argv, fun_argc,
                                               vty, fd, flag);

        /*Count daemon responded */
        if (!rc)
        {
            VLOG_DBG("daemon :%s displayed zlog logging configuration , rc:%d",
                        iter_daemon->name,rc);
        }
        else
        {
            VLOG_ERR("daemon :%s failed to display zlog logging configurations, rc:%d",
                        iter_daemon->name,rc);
        }
        iter_daemon = iter_daemon->next;
    }
    return CMD_SUCCESS;
}

static int
ospf_debug(const char **argv, int argc, int flag)
{
    int fun_argc;
    int fd = -1;
    int rc = 0;
    struct feature* iter = feature_head;
    struct daemon* iter_daemon = NULL;
    char *fun_argv[argc];

    fun_argc = argc;
    if((argc < 2)||(argv == NULL)||(argc > 5))
    {
       VLOG_ERR("Invalid argument list ");
       return   CMD_WARNING ;
    }
    fun_argv[0] = (char *)  argv[0];
    fun_argv[1] = (char *)  argv[1];

    switch (argc)
    {
       case 5:
           fun_argv[4] = (char *)  argv[4];
       case 4:
           fun_argv[3] = (char *)  argv[3];
       case 3:
           fun_argv[2] = (char *)  argv[2];
       default: break;
    }

    if (!initialized)
    {
        feature_head  = get_feature_mapping();
        if ( feature_head == NULL )
        {
            vty_out(vty,"%s%s", ERR_STR ,VTY_NEWLINE);
            return  CMD_WARNING ;
        }
        else
        {
            initialized = 1;
        }
    }

    /* traverse linkedlist to find node */
    for (iter = feature_head ; iter &&
               strcmp_with_nullcheck(iter->name, argv[0]); iter = iter->next);

    VLOG_DBG("feature:%s , desc:%s",STR_NULL_CHK(iter->name),
                STR_NULL_CHK(iter->desc));

    iter_daemon = iter->p_daemon;
    while(iter_daemon)
    {
        rc = vtysh_set_ospf_debug(iter_daemon->name, fun_argv, fun_argc,
                                               vty, fd, flag);
        /*Count daemon responded */
        if (!rc)
        {
            VLOG_DBG("daemon :%s zlog logging configuration , rc:%d",
                        iter_daemon->name,rc);
        }
        else
        {
            VLOG_ERR("daemon :%s failed, zlog logging configurations , rc:%d",
                       iter_daemon->name,rc);
        }
        iter_daemon = iter_daemon->next;
    }
    return CMD_SUCCESS;
}

DEFUN (debug_ospf_packet,
       debug_ospf_packet_all_cmd,
       "debug ospfv2 packet (hello|dd|ls-request|ls-update|ls-ack|all)",
       DBG_STR
       OSPF_STR
       OSPFv2_PACKETS
       OSPFv2_HELLO
       OSPFv2_DB_DESC
       OSPFv2_LINK_STATE_REQ
       OSPFv2_LINK_STATE_UPD
       OSPFv2_Link_STATE_ACK
       OSPFv2_All_PACKETS)
{
    return ospf_debug(argv, argc, 0);
}

ALIAS (debug_ospf_packet,
       debug_ospf_packet_send_recv_cmd,
       "debug ospfv2 packet (hello|dd|ls-request|ls-update|ls-ack|all) (send|recv|detail)",
       DBG_STR
       OSPF_STR
       OSPFv2_PACKETS
       OSPFv2_HELLO
       OSPFv2_DB_DESC
       OSPFv2_LINK_STATE_REQ
       OSPFv2_LINK_STATE_UPD
       OSPFv2_Link_STATE_ACK
       OSPFv2_All_PACKETS
       OSPFv2_PACKET_SENT
       OSPFv2_PACKET_RECV
       OSPFv2_DETAIL_INFO)

ALIAS (debug_ospf_packet,
       debug_ospf_packet_send_recv_detail_cmd,
       "debug ospfv2 packet (hello|dd|ls-request|ls-update|ls-ack|all) (send|recv) detail",
       DBG_STR
       OSPF_STR
       OSPFv2_PACKETS
       OSPFv2_HELLO
       OSPFv2_DB_DESC
       OSPFv2_LINK_STATE_REQ
       OSPFv2_LINK_STATE_UPD
       OSPFv2_Link_STATE_ACK
       OSPFv2_All_PACKETS
       OSPFv2_PACKET_SENT
       OSPFv2_PACKET_RECV
       OSPFv2_DETAIL_INFO)

DEFUN (no_debug_ospf_packet,
       no_debug_ospf_packet_all_cmd,
       "no debug ospfv2 packet (hello|dd|ls-request|ls-update|ls-ack|all)",
       NO_STR
       DBG_STR
       OSPF_STR
       OSPFv2_PACKETS
       OSPFv2_HELLO
       OSPFv2_DB_DESC
       OSPFv2_LINK_STATE_REQ
       OSPFv2_LINK_STATE_UPD
       OSPFv2_Link_STATE_ACK
       OSPFv2_All_PACKETS)
{
    return ospf_debug(argv, argc, 2);
}

ALIAS (no_debug_ospf_packet,
       no_debug_ospf_packet_send_recv_cmd,
       "no debug ospfv2 packet (hello|dd|ls-request|ls-update|ls-ack|all) (send|recv|detail)",
       NO_STR
       DBG_STR
       OSPF_STR
       OSPFv2_PACKETS
       OSPFv2_HELLO
       OSPFv2_DB_DESC
       OSPFv2_LINK_STATE_REQ
       OSPFv2_LINK_STATE_UPD
       OSPFv2_Link_STATE_ACK
       OSPFv2_All_PACKETS
       OSPFv2_PACKET_SENT
       OSPFv2_PACKET_RECV
       OSPFv2_DETAIL_INFO)

ALIAS (no_debug_ospf_packet,
       no_debug_ospf_packet_send_recv_detail_cmd,
       "no debug ospfv2 packet (hello|dd|ls-request|ls-update|ls-ack|all) (send|recv) detail",
       NO_STR
       DBG_STR
       OSPF_STR
       OSPFv2_PACKETS
       OSPFv2_HELLO
       OSPFv2_DB_DESC
       OSPFv2_LINK_STATE_REQ
       OSPFv2_LINK_STATE_UPD
       OSPFv2_Link_STATE_ACK
       OSPFv2_All_PACKETS
       OSPFv2_PACKET_SENT
       OSPFv2_PACKET_RECV
       OSPFv2_DETAIL_INFO)

DEFUN (debug_ospf_ism,
       debug_ospf_ism_cmd,
       "debug (ospfv2) (ism)",
       DBG_STR
       OSPF_STR
       OSPFv2_ISM)
{
    return ospf_debug(argv, argc, 0);
}

ALIAS (debug_ospf_ism,
       debug_ospf_ism_sub_cmd,
       "debug ospfv2 ism (status|events|timers)",
       DBG_STR
       OSPF_STR
       OSPFv2_ISM
       OSPFv2_ISM_STAT_INFO
       OSPFv2_ISM_EVT_INFO
       OSPFv2_ISM_TIMER_INFO)

DEFUN (no_debug_ospf_ism,
       no_debug_ospf_ism_cmd,
       "no debug (ospfv2) (ism)",
       NO_STR
       DBG_STR
       OSPF_STR
       OSPFv2_ISM)
{
    return ospf_debug(argv, argc, 2);
}

ALIAS (no_debug_ospf_ism,
       no_debug_ospf_ism_sub_cmd,
       "no debug ospfv2 ism (status|events|timers)",
       NO_STR
       DBG_STR
       OSPF_STR
       OSPFv2_ISM
       OSPFv2_ISM_STAT_INFO
       OSPFv2_ISM_EVT_INFO
       OSPFv2_ISM_TIMER_INFO)

DEFUN (debug_ospf_nsm,
       debug_ospf_nsm_cmd,
       "debug ospfv2 nsm",
       DBG_STR
       OSPF_STR
       OSPFv2_NSM)
{
    return ospf_debug(argv, argc, 0);
}

ALIAS (debug_ospf_nsm,
       debug_ospf_nsm_sub_cmd,
       "debug ospfv2 nsm (status|events|timers)",
       DBG_STR
       OSPF_STR
       OSPFv2_NSM
       OSPFv2_NSM_STAT_INFO
       OSPFv2_NSM_EVT_INFO
       OSPFv2_NSM_TIMER_INFO)

DEFUN (no_debug_ospf_nsm,
       no_debug_ospf_nsm_cmd,
       "no debug ospfv2 nsm",
       NO_STR
       DBG_STR
       OSPF_STR
       OSPFv2_NSM)
{
    return ospf_debug(argv, argc, 2);
}

ALIAS (no_debug_ospf_nsm,
       no_debug_ospf_nsm_sub_cmd,
       "no debug ospfv2 nsm (status|events|timers)",
       NO_STR
       DBG_STR
       OSPF_STR
       OSPFv2_NSM
       OSPFv2_NSM_STAT_INFO
       OSPFv2_NSM_EVT_INFO
       OSPFv2_NSM_TIMER_INFO)

DEFUN (debug_ospf_lsa,
       debug_ospf_lsa_cmd,
       "debug ospfv2 lsa",
       DBG_STR
       OSPF_STR
       OSPFv2_LSA)
{
    return ospf_debug(argv, argc, 0);
}

ALIAS (debug_ospf_lsa,
       debug_ospf_lsa_sub_cmd,
       "debug ospfv2 lsa (generate|flooding|install|refresh)",
       DBG_STR
       OSPF_STR
       OSPFv2_LSA
       OSPFv2_LSA_GEN
       OSPFv2_LSA_FLOOD
       OSPFv2_LSA_INST
       OSPFv2_LSA_REF)

DEFUN (no_debug_ospf_lsa,
       no_debug_ospf_lsa_cmd,
       "no debug ospfv2 lsa",
       NO_STR
       DBG_STR
       OSPF_STR
       OSPFv2_LSA)
{
    return ospf_debug(argv, argc, 2);
}

ALIAS (no_debug_ospf_lsa,
       no_debug_ospf_lsa_sub_cmd,
       "no debug ospfv2 lsa (generate|flooding|install|refresh)",
       NO_STR
       DBG_STR
       OSPF_STR
       OSPFv2_LSA
       OSPFv2_LSA_GEN
       OSPFv2_LSA_FLOOD
       OSPFv2_LSA_INST
       OSPFv2_LSA_REF)

DEFUN (debug_ospf_event,
       debug_ospf_event_cmd,
       "debug ospfv2 event",
       DBG_STR
       OSPF_STR
       OSPFv2_EVT_INFO)
{
    return ospf_debug(argv, argc, 0);
}

DEFUN (no_debug_ospf_event,
       no_debug_ospf_event_cmd,
       "no debug ospfv2 event",
       NO_STR
       DBG_STR
       OSPF_STR
       OSPFv2_EVT_INFO)
{
    return ospf_debug(argv, argc, 2);
}

DEFUN (debug_ospf_nssa,
       debug_ospf_nssa_cmd,
       "debug ospfv2 nssa",
       DBG_STR
       OSPF_STR
       OSPFv2_NSSA_INFO)
{
    return ospf_debug(argv, argc, 0);
}

DEFUN (no_debug_ospf_nssa,
       no_debug_ospf_nssa_cmd,
       "no debug ospfv2 nssa",
       NO_STR
       DBG_STR
       OSPF_STR
       OSPFv2_NSSA_INFO)
{
    return ospf_debug(argv, argc, 2);
}

DEFUN (debug_ospf_intf_redst,
       debug_ospf_intf_redst_cmd,
       "debug ospfv2 (interface|redistribute)",
       DBG_STR
       OSPF_STR
       OSPFv2_INTF_INFO
       OSPFv2_REDIST_INFO)
{
    return ospf_debug(argv, argc, 0);
}

DEFUN (no_debug_ospf_intf_redst,
       no_debug_ospf_intf_redst_cmd,
       "no debug ospfv2 (interface|redistribute)",
       NO_STR
       DBG_STR
       OSPF_STR
       OSPFv2_INTF_INFO
       OSPFv2_REDIST_INFO)
{
    return ospf_debug(argv, argc, 2);
}
