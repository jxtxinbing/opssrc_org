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

#ifndef __VRFMGRD_H__
#define __VRFMGRD_H__

#include <openvswitch/vlog.h>
#include <openvswitch/compiler.h>

#define MAX_VRF_ID 1023
#define DEFAULT_VRF_ID 0
#define MIN_VRF_ID 1

extern void vrfmgrd_ovsdb_init(const char *db_path);
extern void vrfmgrd_ovsdb_exit(void);
extern void vrfmgrd_run(void);
extern void vrfmgrd_wait(void);
bool allocate_vrf_id(struct ovsrec_vrf *vrf, uint32_t vrf_id);
bool free_vrf_allocated_id(uint32_t vrf_id);
void initialize_free_vrf_id_list(void);
void set_vrf_id(int64_t vrf_id);
int32_t allocate_first_vrf_id(struct ovsrec_vrf *vrf);

/*
 * key : "namespace_ready" is used in status column of VRF table
 * value : "true" is set to indicate if namespace is created for VRF
 */
#define NAMESPACE_READY      "namespace_ready"
#define VRF_NAMESPACE_TRUE   "true"

#define NAMESPACE_ADD        "ip netns add"
#define NAMESPACE_DELETE     "ip netns delete"
#define NAMESPACE_EXEC       "ip netns exec"
#define SET_INTERFACE        "ip link set"
#define SWNS_NAMESPACE       "swns"
#define NETWORK_NAMESPACE    "netns"
#define SPACE                " "
#define RUN_ZEBRA            "/usr/sbin/ops-zebra --detach -vSYSLOG:INFO &"
#define MAX_ARRAY_SIZE       100

#endif /* __VRFMGRD_H__ */
/** @} end of group ops-intfd */
