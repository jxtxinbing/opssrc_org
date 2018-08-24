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
 * @defgroup nl_utils Core Utilities
 * This library provides common utility functions used by various OpenSwitch
 * processes.
 * @{
 *
 * @defgroup nl_utils_public Public Interface
 * Public API for nl_utils library.
 *
 *
 *
 * @{
 *
 * @file
 * Header for nl_utils library.
 ***************************************************************************/

#ifndef __NETLINK_UTILS_H_
#define __NETLINK_UTILS_H_

#include <linux/netlink.h>
#include <linux/rtnetlink.h>
#include <fcntl.h>
#include <sched.h>
#include <stdbool.h>
#include <net/if.h>

#define MAX_BUFFER_SIZE        128
#define MAX_BUFFER_LENGTH      128
#define SWITCH_NAMESPACE       "swns"

/**************************************************************************
***************************************************************************/
struct setns_info
{
    char from_ns[MAX_BUFFER_SIZE];
    char to_ns[MAX_BUFFER_SIZE];
    char intf_name[MAX_BUFFER_SIZE];
};

/**************************************************************************
***************************************************************************/
struct nl_sock_params
{
    int family;
    int type;
    int protocol;
};

typedef enum nlutils_op
{
  NLUTILS_SOCKET_CREATE,
  NLUTILS_IFINDEX_TO_NAME,
  NLUTILS_IFNAME_TO_INDEX,
  NLUTILS_MAX_OP
}nlutils_op;


/**************************************************************************
***************************************************************************/
struct nlutils_op_data
{
    char         ns_name[MAX_BUFFER_SIZE];
    nlutils_op   operation;
    union {
        struct nl_sock_params *s;
        struct {
            int ifindex;
            char ifname[IFNAMSIZ];
        }in;
        struct {
            char ifname[IFNAMSIZ];
            int ifindex;
        }ni;
    }params;
    int result;
};

struct rtareq {
    struct nlmsghdr  n;
    struct ifinfomsg i;
    char buf[128];      /* must fit interface name length (IFNAMSIZ)*/
};

/************************************************************************
* moves an interface from another namespace to default_vrf namespace
*
* @param[in]  setns_local_info : contains from and to vrf names and intf name
*
* @return true if sucessful, else false on failure
***************************************************************************/
extern bool nl_move_intf_to_vrf(struct setns_info *setns_local_info);
/***************************************************************************
* creates an socket by entering the corresponding namespace
*
* @param[in]  ns_name : this is the namespace in which socket to be opened.
* @param[in]  params : contains socket params to pass to the socket.
*
* @return valid fd if sucessful, else 0 on failure
***************************************************************************/
extern int nl_create_ns_socket(char* ns_name, struct nl_sock_params *params);
/***************************************************************************
* creates an socket by entering the corresponding namespace
*
* @param[in]  ns_name : this is the namespace in which socket to be opened.
* @param[in]  socket_fd : fd of the socket to close.
*
* @return valid true if sucessful, else false on failure
***************************************************************************/
extern bool nl_close_ns_socket(char* ns_name, int socket_fd);

/***************************************************************************
* Retrieves the if name from the ifindex in given namespace
*
* @param[in]  ifindex : ifindex for which the ifname to be retrieved.
* @param[in]  ns_name : this is the namespace in which search to be performed.
*
* @param[out]  if_name : this is the ifname corresponding to the ifindex.
* @return 0 if sucessful, else -1 on failure
***************************************************************************/
unsigned int nl_if_indextoname(const int ifindex, char *if_name,
                               const char *ns_name);
/***************************************************************************
* Retrieves the if index from the ifname in given namespace
*
* @param[in]  if_name : for which the ifindex to be retrieved.
* @param[in]  ns_name : this is the namespace in which search to be performed.
*
* @return valid ifindex if sucessful, else 0 on failure
***************************************************************************/
unsigned int nl_if_nametoindex(const char *ns_name, const char* if_name);

/***************************************************************************
* type of action to be performed inside the thread
*
* @param[in]  tdata : struct nlutils_op_data parameter for parsing
*
* executes desired operation and stores the result in tdata itself
***************************************************************************/
void nl_perform_socket_operation(struct nlutils_op_data *tdata);

/***************************************************************************
 * enters a namespace with the given ns name
 *
 * @param[in]  ns_name  : the namespace name corresponding to given namespace.
 *
 * @return 0 if sucessful, else negative value on failure
 ***************************************************************************/
int nl_setns_with_name(const char *ns_name);

/***************************************************************************
 * enters mgmt OOBM namespace
 *
 * @return 0 if sucessful, else negative value on failure
 ***************************************************************************/
int nl_setns_oobm(void);
#endif /* __NETLINK_UTILS_H_ */
/** @} end of group nl_utils_public */
/** @} end of group nl_utils */
