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
 * @ingroup nl_utils
 * This module contains the DEFINES and functions that comprise the nl-utils
 * library.
 *
 * @file
 * Source file for nl-utils library.
 *
 ****************************************************************************/

#define _GNU_SOURCE
#include <err.h>
#include <errno.h>
#include <getopt.h>
#include <limits.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <sched.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <dynamic-string.h>

#include <assert.h>
#include "openswitch-idl.h"
#include "nl-utils.h"
#include "openvswitch/vlog.h"

VLOG_DEFINE_THIS_MODULE(nl_utils);

/***************************************************************************
* type of action to be performed inside the thread
*
* @param[in]  tdata : struct nlutils_op_data parameter for parsing
*
* executes desired operation and stores the result in tdata itself
***************************************************************************/
void nl_perform_socket_operation(struct nlutils_op_data *tdata)
{
   int ns_sock = -1;
   switch (tdata->operation)
   {
       case NLUTILS_SOCKET_CREATE:
           /* Open a socket in the namespace set by thread */
           ns_sock = socket(tdata->params.s->family,
                            tdata->params.s->type,
                            tdata->params.s->protocol);

           if (ns_sock < 0) {
               VLOG_ERR("socket creation failed (%s) in namespace %s",
                                      strerror(errno), tdata->ns_name);
           }
           tdata->result=ns_sock;
           break;
       case NLUTILS_IFINDEX_TO_NAME:
           if_indextoname(tdata->params.in.ifindex, tdata->params.in.ifname);
           tdata->result=0;
           break;
       case NLUTILS_IFNAME_TO_INDEX:
           tdata->params.ni.ifindex = if_nametoindex(tdata->params.ni.ifname);
           tdata->result=0;
           break;
       default:
           VLOG_ERR("unsupported op %d in ns name %s",
                                       tdata->operation, tdata->ns_name);
           break;
   }
   return;
}


/***************************************************************************
 * check if the ns_name is default namespace or not.
 *
 * @param[in]  ns_name  : the namespace name to used for comparision.
 *
 * @return 0 if default namespace, else 1
 ***************************************************************************/
static bool nl_is_nondefault_ns(const char *ns_name)
{
     if (!ns_name
         || strncmp(ns_name, SWITCH_NAMESPACE, strlen(SWITCH_NAMESPACE)) == 0)
     {
        /* DEFAULT namespace. ignore entering this namespace again */
        return 0;
     }
     return 1;
}

/***************************************************************************
* creates an socket by entering the corresponding namespace by spawning the
* thread.
*
* @param[in]  ns_name : this is the namespace in which socket to be opened.
* @param[in]  socket_fd : fd of the socket to close.
*
* @return valid true if sucessful, else false on failure
***************************************************************************/
int  nl_create_ns_socket(char* ns_name, struct nl_sock_params *params)
{
    struct nlutils_op_data tdata;
    bool non_default_ns = nl_is_nondefault_ns(ns_name);

    snprintf(tdata.ns_name, MAX_BUFFER_SIZE-1, "%s", ns_name);
    tdata.operation = NLUTILS_SOCKET_CREATE;
    tdata.params.s = params;
    if (non_default_ns)
    {
        nl_setns_with_name(ns_name);
    }
    nl_perform_socket_operation(&tdata);
    if (non_default_ns)
    {
        nl_setns_with_name(SWITCH_NAMESPACE);
    }

    return tdata.result;
}

/***************************************************************************
* creates an socket by entering the corresponding namespace
*
* @param[in]  ns_name : this is the namespace in which socket to be opened.
* @param[in]  params : contains socket params to pass to the socket.
*
* @return valid fd if sucessful, else 0 on failure
***************************************************************************/
bool nl_close_ns_socket (char* ns_name, int socket_fd)
{
    /* delete the socket created by the thread */
    close(socket_fd);

    VLOG_DBG("socket closed fd = %d in namespace %s", socket_fd, ns_name);

    return true;
}

/***************************************************************************
 * enters a namespace with the given ns name
 *
 * @param[in]  ns_name  : the namespace name corresponding to given namespace.
 *
 * @return 0 if sucessful, else negative value on failure
 ***************************************************************************/
int nl_setns_with_name (const char *ns_name)
{
     int fd = -1;
     char ns_path[MAX_BUFFER_SIZE] = {0};

     strcat(ns_path, "/var/run/netns/");
     snprintf(ns_path + strlen(ns_path), MAX_BUFFER_SIZE - strlen(ns_path) - 1,
                                                                 "%s", ns_name);
     fd = open(ns_path, O_RDONLY);  /* Get descriptor for namespace */
     if (fd == -1)
     {
         VLOG_ERR("%s: namespace does not exist, errno %d\n", ns_name, errno);
         return -1;
     }

     if (setns(fd, CLONE_NEWNET) == -1) /* Join that namespace */
     {
         VLOG_ERR("Unable to set namespace %s in the thread, error %d",
                    ns_name, errno);
         close(fd);
         return -1;
     }

    close(fd);
    return 0;
}

/************************************************************************
* moves an interface from one namespace to another namespace.
*
* @param[in]  setns_local_info : contains from and to ns names and intf name
*
* @return true if sucessful, else false on failure
***************************************************************************/
bool nl_move_intf_to_vrf (struct setns_info *setns_local_info)
{
    char ns_path[MAX_BUFFER_SIZE]= {0};
    char set_ns[MAX_BUFFER_SIZE] = {0};
    int fd = -1, fd_from_ns = -1;
    struct rtattr *rta;
    struct rtareq req;
    int ifindex;

    int ns_sock = -1;
    bool rc = false;
    struct sockaddr_nl s_addr;

    /* open a FD to move the interface */
    snprintf(ns_path, sizeof(ns_path), "/var/run/netns/%s",
                                                       setns_local_info->to_ns);
    fd = open(ns_path, O_RDONLY);
    if (fd == -1) {
        VLOG_ERR("Unable to open fd for namepsace %s, errno %d",
                       setns_local_info->to_ns, errno);
        goto cleanup;
    }

    /* Open FD to set the namespace */

    snprintf(set_ns, sizeof(set_ns), "/var/run/netns/%s",
                                                     setns_local_info->from_ns);
    fd_from_ns = open(set_ns, O_RDONLY);
    if (fd_from_ns == -1) {
        VLOG_ERR("Unable to open fd for namepsace %s errno %d",
                                             setns_local_info->from_ns, errno);
        goto cleanup;
    }
    if (nl_is_nondefault_ns(setns_local_info->from_ns) &&
              nl_setns_with_name(setns_local_info->from_ns)) {
        VLOG_ERR("Unable to set %s new namespace, errno %d",
                                       setns_local_info->from_ns, errno);
        goto cleanup;
    }
    /* Open a socket in the namespace */
    ns_sock = socket(AF_NETLINK, SOCK_RAW, NETLINK_ROUTE);
    ifindex = if_nametoindex(setns_local_info->intf_name);

    if (nl_is_nondefault_ns(setns_local_info->from_ns) &&
              nl_setns_with_name(SWITCH_NAMESPACE)) {
        VLOG_ERR("Unable to set %s old namespace, errno %d",
                                      setns_local_info->to_ns, errno);
        goto cleanup;
    }

    if (ns_sock < 0) {
        VLOG_ERR("Netlink socket creation failed (%s) in namespace %s",
                                    strerror(errno), setns_local_info->from_ns);
        goto cleanup;
    }

    memset((void *) &s_addr, 0, sizeof(s_addr));
    s_addr.nl_family = AF_NETLINK;
    s_addr.nl_pid = getpid();
    s_addr.nl_groups = RTMGRP_IPV4_IFADDR | RTMGRP_IPV6_IFADDR | RTMGRP_LINK;

    if (bind(ns_sock, (struct sockaddr *) &s_addr, sizeof(s_addr)) < 0) {
        if (errno != EADDRINUSE) {
            VLOG_ERR("Netlink socket bind failed (%s) in namespace %s",
                                    strerror(errno), setns_local_info->from_ns);
            goto cleanup;
        }
    }

    VLOG_DBG("Netlink socket created. fd = %d",ns_sock);

    memset(&req, 0, sizeof(req));

    req.n.nlmsg_len     = NLMSG_SPACE(sizeof(struct ifinfomsg));
    req.n.nlmsg_pid     = getpid();
    req.n.nlmsg_type    = RTM_SETLINK;
    req.n.nlmsg_flags   = NLM_F_REQUEST;

    req.i.ifi_family    = AF_UNSPEC;
    req.i.ifi_index     = ifindex;

    if (req.i.ifi_index == 0) {
        VLOG_ERR("Unable to get ifindex for interface: %s, errno %d",
                                          setns_local_info->intf_name, errno);
        goto cleanup;
    }

    rc = true;
    req.i.ifi_change = 0xffffffff;
    rta = (struct rtattr *)(((char *) &req) + NLMSG_ALIGN(req.n.nlmsg_len));
    rta->rta_type = IFLA_NET_NS_FD;
    rta->rta_len = RTA_LENGTH(sizeof(unsigned int));
    req.n.nlmsg_len = NLMSG_ALIGN(req.n.nlmsg_len) + RTA_LENGTH(sizeof(fd));
    memcpy(RTA_DATA(rta), &fd, sizeof(fd));

    if (send(ns_sock, &req, req.n.nlmsg_len, 0) == -1) {
        VLOG_ERR("Netlink failed to set fd %d for interface %s, errno %d", fd,
                 setns_local_info->intf_name, errno);
        rc = false;
    }
cleanup:
    if (fd != -1) { close(fd);}
    if (ns_sock != -1) { close(ns_sock);}
    if (fd_from_ns != -1) {close(fd_from_ns);}
    return rc;
}

/***************************************************************************
* Retrieves the if index from the ifname in given namespace
*
* @param[in]  if_name : for which the ifindex to be retrieved.
* @param[in]  ns_name : this is the namespace in which search to be performed.
*
* @return valid ifindex if sucessful, else 0 on failure
***************************************************************************/
unsigned int nl_if_nametoindex(const char *ns_name, const char* if_name)
{
    unsigned int ifindex = 0;
    struct nlutils_op_data tdata;
    bool non_default_ns = nl_is_nondefault_ns(ns_name);

    snprintf(tdata.ns_name, MAX_BUFFER_SIZE-1, "%s", ns_name);
    snprintf(tdata.params.ni.ifname, IFNAMSIZ-1, "%s", if_name);
    tdata.operation = NLUTILS_IFNAME_TO_INDEX;
    if (non_default_ns)
    {
        nl_setns_with_name(ns_name);
    }
    nl_perform_socket_operation(&tdata);
    ifindex = tdata.params.ni.ifindex;
    if (non_default_ns)
    {
        nl_setns_with_name(SWITCH_NAMESPACE);
    }

    return ifindex;
}

/***************************************************************************
* Retrieves the if name from the ifindex in given namespace
*
* @param[in]  ifindex : ifindex for which the ifname to be retrieved.
* @param[in]  ns_name : this is the namespace in which search to be performed.
*
* @param[out]  if_name : this is the ifname corresponding to the ifindex.
* @return 0 if sucessful, else -1 on failure
***************************************************************************/
unsigned int
nl_if_indextoname (const int ifindex, char *if_name, const char *ns_name)
{
    struct nlutils_op_data tdata;
    bool non_default_ns = nl_is_nondefault_ns(ns_name);

    snprintf(tdata.ns_name, MAX_BUFFER_SIZE-1, "%s", ns_name);
    tdata.params.in.ifindex = ifindex;
    tdata.operation = NLUTILS_IFINDEX_TO_NAME;
    if (non_default_ns)
    {
        nl_setns_with_name(ns_name);
    }
    nl_perform_socket_operation(&tdata);
    snprintf(if_name, IFNAMSIZ-1, "%s", tdata.params.in.ifname);
    if (non_default_ns)
    {
        nl_setns_with_name(SWITCH_NAMESPACE);
    }

    return 0;
}

/***************************************************************************
 * enters OOBM namespace
 *
 * @return 0 if sucessful, else negative value on failure
 ***************************************************************************/
int nl_setns_oobm (void)
{
    int fd = -1;
    char ns_path[MAX_BUFFER_SIZE] = {0};

    snprintf(ns_path, MAX_BUFFER_SIZE, "/proc/1/ns/net");
    fd = open(ns_path, O_RDONLY);
    if (fd == -1)
    {
        VLOG_ERR("Entering mgmt OOBM namespace: errno %d", errno);
        return -1;
    }

    if (setns(fd, CLONE_NEWNET) == -1) /* Join that namespace */
    {
        VLOG_ERR("Unable to enter the mgmt OOBM namespace, errno %d", errno);
        close(fd);
        return -1;
    }
    close(fd);
    return 0;
}
