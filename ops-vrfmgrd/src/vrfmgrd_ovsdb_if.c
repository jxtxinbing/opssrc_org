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
/************************************************************************//**
 * @ingroup vrfmgrdd
 *
 * @file
 * Source for vrfmgrd OVSDB access interface.
 * Creates a namespace and deletes a namespace.
 * Starts a zebra process in the namespace.
 * Move interfaces to default namesapce on a VRF deletion.
 *
 ***************************************************************************/
#define _GNU_SOURCE
#include <sched.h>

#include <errno.h>
#include <getopt.h>
#include <limits.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <ctype.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <fcntl.h>

#include <config.h>
#include <command-line.h>
#include <compiler.h>
#include <daemon.h>
#include <dirs.h>
#include <dynamic-string.h>
#include <fatal-signal.h>
#include <ovsdb-idl.h>
#include <poll-loop.h>
#include <unixctl.h>
#include <util.h>
#include <openvswitch/vconn.h>
#include <openvswitch/vlog.h>
#include <vswitch-idl.h>
#include <openswitch-idl.h>
#include <hash.h>
#include <shash.h>
#include <unistd.h>
#include "vrfmgrd.h"
#include "smap.h"
#include "uuid.h"
#include "vrf-utils.h"

VLOG_DEFINE_THIS_MODULE(vrfmgrd_ovsdb_if);

/* Mapping of all the vrf's */
static struct shash all_vrfs = SHASH_INITIALIZER(&all_vrfs);
/*
 * Structure to store port names belonging to a vrf.
 */
struct port_name {
    char *name; /* To store port name belongin to a VRF*/
};

/*
 * Local cache to save vrf and port table information
 */
struct vrf_info {
    struct uuid       *vrf_uuid; /*vrf_uuid is pointing to uuid sttucture
                                   refer to uuid.h for further info*/
    char              *name;    /*VRF name*/
    char              *ns_name; /*VRF ns name, remember for delete*/
    size_t            n_ports;  /*number of ports associated with VRF*/
    struct port_name  **ports;  /*to store port names belongs to VRF*/
    uint32_t          vrf_id;
};

static struct ovsdb_idl *idl;
static unsigned int idl_seqno;

static bool system_configured = false;
static bool commit_txn = false;
static int
reconfigure_ports(struct vrf_info *modify_vrf_ports,
                  const struct ovsrec_vrf *vrf_row);

/* Create a connection to the OVSDB at db_path and create a DB cache
 * for this daemon. */
void
vrfmgrd_ovsdb_init(const char *db_path)
{
    /* Initialize IDL through a new connection to the DB. */
    idl = ovsdb_idl_create(db_path, &ovsrec_idl_class, false, true);
    if (idl == NULL) {
        idl = ovsdb_idl_create(db_path, &ovsrec_idl_class, false, true);
    }
    idl_seqno = ovsdb_idl_get_seqno(idl);
    ovsdb_idl_set_lock(idl, "ops_vrfmgrd");

    /* Reject writes to columns which are not marked write-only using
     * ovsdb_idl_omit_alert(). */
    ovsdb_idl_verify_write_only(idl);

    /* Monitor system table to check for cur_cfg value */
    ovsdb_idl_add_table(idl, &ovsrec_table_system);
    ovsdb_idl_add_column(idl, &ovsrec_system_col_cur_cfg);
    ovsdb_idl_add_column(idl, &ovsrec_system_col_vrfs);

    /* Monitor the following columns of VRF, marking them read-only. */
    ovsdb_idl_add_table(idl, &ovsrec_table_vrf);
    ovsdb_idl_add_column(idl, &ovsrec_vrf_col_name);
    ovsdb_idl_add_column(idl, &ovsrec_vrf_col_ports);
    ovsdb_idl_add_column(idl, &ovsrec_vrf_col_table_id);
    ovsdb_idl_omit_alert(idl, &ovsrec_vrf_col_table_id);
    ovsdb_idl_add_column(idl, &ovsrec_vrf_col_status);
    ovsdb_idl_omit_alert(idl, &ovsrec_vrf_col_status);

    /* Monitor the following columns of port table, marking them read-only. */
    ovsdb_idl_add_table(idl, &ovsrec_table_port);
    ovsdb_idl_add_column(idl, &ovsrec_port_col_name);

    initialize_free_vrf_id_list();
} /* vrfmgrd_ovsdb_init */

void
vrfmgrd_ovsdb_exit(void)
{
    ovsdb_idl_destroy(idl);
} /* vrfmgrd_ovsdb_exit */

/*
 * Creates a new network namespace of name ns_name
 * using unshare and mount.
 */
static void
create_namespace(const char *ns_name)
{
    char ns_path[MAX_ARRAY_SIZE] = {0};
    char if_path[MAX_ARRAY_SIZE] = {0};
    FILE *fp;

    snprintf(ns_path, MAX_ARRAY_SIZE, "%s/%s", "/var/run/netns", ns_name);
    close(open(ns_path, O_RDONLY|O_CREAT|O_EXCL, 0));
    unshare(CLONE_NEWNET);
    mount("/proc/self/ns/net", ns_path, "none", MS_BIND , NULL);

    /* Bring up default loopback for self ping to work */
    snprintf(if_path, MAX_ARRAY_SIZE, "/sbin/ip netns exec %s ifconfig lo up", ns_name);
    fp = popen(if_path, "r");
    if (fp == NULL) {
        VLOG_ERR("Command failed with popen");
        return;
    }
    pclose(fp);

    return;
}

/*
 * Updates local vrf_info structre and creates a namespace
 * when a new VRF is inserted to OVSDB.
 */
static int
vrf_create_namespace(struct ovsrec_vrf *vrf)
{
    struct vrf_info *new_vrf = NULL;
    char run_exec[MAX_ARRAY_SIZE] = {0}, buff[UUID_LEN+1] = {0};
    int vrf_id;
    FILE *fp;
    bool config_restart = false;

    new_vrf = xzalloc(sizeof(struct vrf_info));
    config_restart = ((vrf->table_id == NULL) ? false: true);
    if(config_restart)
    {
        set_vrf_id(*vrf->table_id);
    }
    else
    {
        vrf_id = allocate_first_vrf_id(vrf);
        if (vrf_id < 0)
        {
            VLOG_DBG("%s: no table_id available, VRF creation failed.\n", vrf->name);
            free(new_vrf);
            new_vrf = NULL;
            return -1;
        }
    }
    new_vrf->vrf_id = (uint32_t) *vrf->table_id;

    new_vrf->vrf_uuid = xzalloc(sizeof(struct uuid));
    sprintf(buff, UUID_FMT, UUID_ARGS(&(vrf->header_.uuid)));

    new_vrf->vrf_uuid->parts[0] = vrf->header_.uuid.parts[0];
    new_vrf->vrf_uuid->parts[1] = vrf->header_.uuid.parts[1];
    new_vrf->vrf_uuid->parts[2] = vrf->header_.uuid.parts[2];
    new_vrf->vrf_uuid->parts[3] = vrf->header_.uuid.parts[3];
    new_vrf->name = xstrdup(vrf->name);
    new_vrf->ports = NULL;
    new_vrf->n_ports = 0;
    reconfigure_ports(new_vrf, vrf); //populate vrf structure

    shash_add(&all_vrfs, (const char *)buff, new_vrf);

    /* No need to create a namespace for vrf_default */
    if (!strncmp(vrf->name, DEFAULT_VRF_NAME, strlen(DEFAULT_VRF_NAME)+1)) {
        VLOG_DBG("%s: no namespace need to be created\n", vrf->name);
        return 0;
    }

    get_vrf_ns_from_table_id(idl, new_vrf->vrf_id, &buff[0]);
    new_vrf->ns_name = xstrdup(buff);
    if(!config_restart)
    {
        create_namespace(buff);
    }

    /* In the current desgin zebra is run by vrfmgrd daemon
     * later zebra will be run by systemd
     */
    strncat(run_exec, RUN_ZEBRA, strlen(RUN_ZEBRA));
    fp = popen(run_exec, "r");
    if (fp == NULL) {
        VLOG_ERR("Command failed with popen");
        return -1;
    }
    pclose(fp);
    return 0;
}

/*
 * Gets vrf_info structre of deleted VRF then deletes local cache and namespace
 * when a VRF is deleted from OVSDB.
 */
static int
vrf_delete_namespace(struct shash_node *sh_node)
{
    struct vrf_info *del_vrf = NULL;
    size_t i;
    char ns_path[MAX_ARRAY_SIZE] = {0};

    del_vrf = sh_node->data;

    /*
     * get_vrf_ns_from_table_id won't work in delete path
     * as db would have removed that record. Hence use
     * the stored name
     */
    snprintf(ns_path, MAX_ARRAY_SIZE, "%s/%s",
               "/var/run/netns", del_vrf->ns_name);

    umount2(ns_path, MNT_DETACH);
    VLOG_ERR("umount error %s/%d", strerror(errno), errno);
    unlink(ns_path);
    VLOG_ERR("unlink error %s/%d", strerror(errno), errno);

    for(i = 0 ; i < del_vrf->n_ports ; i++) {
        free(del_vrf->ports[i]->name);
        del_vrf->ports[i]->name = NULL;
        free(del_vrf->ports[i]);
        del_vrf->ports[i]= NULL;
    }

    free(del_vrf->ports);
    free(del_vrf->name);
    free(del_vrf->ns_name);
    free(del_vrf->vrf_uuid);
    if (!free_vrf_allocated_id(del_vrf->vrf_id)){
        VLOG_ERR("Failed to free the VRF assigned ID");
        return -1;
    }
    free(del_vrf);
    del_vrf->ports = NULL;
    del_vrf->name = NULL;
    del_vrf->ns_name = NULL;
    del_vrf->vrf_uuid = NULL;
    del_vrf = NULL;
    VLOG_INFO("Deleted a namespace :%s\n", sh_node->name);
    shash_delete(&all_vrfs, sh_node);
    return 0;
}

/*
 * Update namespace_ready key value pair, when a namespace is created.
 */
static void
update_vrf_ready(struct ovsrec_vrf *vrf)
{
    struct smap smap_vrf_status;

    smap_clone(&smap_vrf_status, &vrf->status);
    smap_add_once(&smap_vrf_status, NAMESPACE_READY, VRF_NAMESPACE_TRUE);

    ovsrec_vrf_set_status(vrf, &smap_vrf_status);
    smap_destroy(&smap_vrf_status);
    return;
}

/*
 * Move interfaces to swns(default) namespace if any interfaces belonging to
 * deleted VRF.
 */
static int
move_intf_to_default_ns(struct vrf_info *move_vrf_intf)
{
    size_t i;

    for (i = 0; i < move_vrf_intf->n_ports; i++) {
        struct setns_info setns_local_info;
        strncpy(&setns_local_info.to_ns[0], SWITCH_NAMESPACE,  strlen(SWITCH_NAMESPACE) + 1);
        snprintf(&setns_local_info.from_ns[0], UUID_LEN+1, move_vrf_intf->ns_name);
        strncpy(&setns_local_info.intf_name[0], move_vrf_intf->ports[i]->name,
                 IFNAMSIZ);
        if (!nl_move_intf_to_vrf(&setns_local_info)) {
            VLOG_ERR("Failed to move interface to %s from %s",
                      SWITCH_NAMESPACE, move_vrf_intf->name);
        }
    }
    return 0;
}

/*
 * Reconfigure ports in local vrf_info cache, if any port is deleted or added
 * to a particular VRF.
 */
static int
reconfigure_ports(struct vrf_info *modify_vrf_ports, const struct ovsrec_vrf *vrf_row)
{
    int i;
    struct port_name *port;

    for(i = 0 ; i < modify_vrf_ports->n_ports ; i++) {
        free(modify_vrf_ports->ports[i]->name);
        modify_vrf_ports->ports[i]->name = NULL;
        free(modify_vrf_ports->ports[i]);
        modify_vrf_ports->ports[i] = NULL;
    }
    modify_vrf_ports->n_ports = vrf_row->n_ports;
    free(modify_vrf_ports->ports);
    modify_vrf_ports->ports = NULL;
    if (vrf_row->n_ports == 0 ) {
        modify_vrf_ports->ports = NULL;
    }
    else {
        modify_vrf_ports->ports = xmalloc(vrf_row->n_ports * sizeof(struct port_name *));
        for (i = 0; i < vrf_row->n_ports ; i++) {
            port = malloc(sizeof(struct port_name));
            if (port == NULL) {
               VLOG_ERR("Memory cannot be allocated to port\n");
               return 0;
            }
            port->name = xstrdup(vrf_row->ports[i]->name);
            if (port->name == NULL) {
               VLOG_ERR("Memory cannot be allocated to port name\n");
               return 0;
            }
            modify_vrf_ports->ports[i] = port;
        }
    }
    return 0;
}

/* Checks to see if:
 * vrf has been added/deleted.
 * port has been added/deleted from a vrf.
 * Perform below functions.
 * create a namespace and delete a namespace.
 * move ports to default namespace when a VRF is deleted.
 */

int vrfmgrd_reconfigure()
{
    const struct ovsrec_vrf *vrf_row = NULL;
    unsigned int new_idl_seqno = 0;
    struct shash sh_idl_vrfs;
    struct shash_node *sh_node = NULL, *sh_next = NULL;

    new_idl_seqno = ovsdb_idl_get_seqno(idl);
    if (new_idl_seqno == idl_seqno) {
        VLOG_DBG("There is no change in idl_seq_no");
        /* There was no change in the DB. */
        return 0;
    }

    /* Get first row pointer to vrf table. */
    vrf_row = ovsrec_vrf_first(idl);

    /* if its not a vrf addition or deletion related operation
     * then do not go ahead.
     */
    if ( (!OVSREC_IDL_ANY_TABLE_ROWS_MODIFIED(vrf_row, idl_seqno)) &&
            (!OVSREC_IDL_ANY_TABLE_ROWS_DELETED(vrf_row, idl_seqno))  &&
            (!OVSREC_IDL_ANY_TABLE_ROWS_INSERTED(vrf_row, idl_seqno)) ) {
        VLOG_DBG("Not a vrf row change\n");
        return 0;
    }

    /* Collect all VRF's from DB if any VRF inserted or deleted*/
    if ( OVSREC_IDL_ANY_TABLE_ROWS_DELETED(vrf_row, idl_seqno) ||
            OVSREC_IDL_ANY_TABLE_ROWS_INSERTED(vrf_row, idl_seqno) ) {
        shash_init(&sh_idl_vrfs);
        OVSREC_VRF_FOR_EACH(vrf_row, idl) {
            char buff[UUID_LEN+1]={0};
            sprintf(buff, UUID_FMT, UUID_ARGS(&(vrf_row->header_.uuid)));
            if (!shash_add_once(&sh_idl_vrfs, (const char *)buff, vrf_row)) {
                VLOG_WARN("vrf %s specified twice", vrf_row->name);
            }
        }
    }

    vrf_row = ovsrec_vrf_first(idl);

    /* Add new VRF namespace*/
    if (OVSREC_IDL_ANY_TABLE_ROWS_INSERTED(vrf_row, idl_seqno)) {
        SHASH_FOR_EACH(sh_node, &sh_idl_vrfs) {
            if (!shash_find_data(&all_vrfs, sh_node->name)) {
                if (vrf_create_namespace(sh_node->data) != -1) {
                    VLOG_INFO("Created a namespace :%s\n",
                               sh_node->name);
                    update_vrf_ready(sh_node->data);
                    commit_txn = true;
                } else {
                    VLOG_INFO("failed to creat a namespace :%s\n",
                               sh_node->name);
                }
            }
        }
        /* Destroy the shash of the IDL VRF's. */
        shash_destroy(&sh_idl_vrfs);
    }

    /* Delete existing VRF namespace*/
    else if (OVSREC_IDL_ANY_TABLE_ROWS_DELETED(vrf_row, idl_seqno)) {
        SHASH_FOR_EACH_SAFE(sh_node, sh_next, &all_vrfs) {
            if (!shash_find_data(&sh_idl_vrfs, sh_node->name)) {
                if(move_intf_to_default_ns(sh_node->data) == -1) {
                    VLOG_ERR("Cannot move interface to default namespace\n");
                }
                else {
                    if(vrf_delete_namespace(sh_node) != -1) {
                        commit_txn = true;
                    }
                }
            }
        }
        /* Destroy the shash of the IDL VRF's. */
        shash_destroy(&sh_idl_vrfs);
    }

    else if (OVSREC_IDL_ANY_TABLE_ROWS_MODIFIED(vrf_row, idl_seqno)) {
        if ((OVSREC_IDL_IS_COLUMN_MODIFIED(ovsrec_vrf_col_ports, idl_seqno))) {
            OVSREC_VRF_FOR_EACH(vrf_row, idl) {
                char buff[UUID_LEN+1]={0};
                struct vrf_info *modify_vrf_ports = NULL;
                sprintf(buff, UUID_FMT, UUID_ARGS(&(vrf_row->header_.uuid)));
                modify_vrf_ports = shash_find_data(&all_vrfs,(const char*)buff);
                if (modify_vrf_ports != NULL) {
                    VLOG_DBG("modification in VRF :%s", vrf_row->name);
                    reconfigure_ports(modify_vrf_ports, vrf_row);
                }
            }
        }
    }
    idl_seqno = new_idl_seqno;
    return 0;
}

/*
 * Check if cur_cfg is set to 1, if yes continue else return and call the
 * function till value is set to 1.
 */
static inline bool
vrfmgrd_system_is_configured(void)
{
    const struct ovsrec_system *sysrow = NULL;
    if (system_configured) {
        return true;
    }

    sysrow = ovsrec_system_first(idl);

    if (sysrow && sysrow->cur_cfg > INT64_C(0)) {
        VLOG_DBG("System now configured (cur_cfg=%" PRId64 ").",
                 sysrow->cur_cfg);
        return (system_configured = true);
    }

    return false;
} /* vrfmgrd_system_is_configured */

void
vrfmgrd_run(void)
{
    struct ovsdb_idl_txn *txn;

    /* Process a batch of messages from OVSDB. */
    ovsdb_idl_run(idl);

    if (ovsdb_idl_is_lock_contended(idl)) {
        static struct vlog_rate_limit rl = VLOG_RATE_LIMIT_INIT(1, 1);

        VLOG_ERR_RL(&rl, "Another vrfmgrd process is running, "
                    "disabling this process until it goes away");

        return;
    } else if (!ovsdb_idl_has_lock(idl)) {
        VLOG_ERR("No lock taken by the vrfmgrd\n");
        return;
    }

    /* Nothing to do until system has been configured, i.e., cur_cfg > 0. */
    if (!vrfmgrd_system_is_configured()) {
        return;
    }

    commit_txn = false;
    /* Update the local configuration and push any changes to the DB. */
    txn = ovsdb_idl_txn_create(idl);

    if (!vrfmgrd_reconfigure()) {
        if (commit_txn) {
            VLOG_DBG("Commiting changes\n");
            /* Some OVSDB write needs to happen. */
            ovsdb_idl_txn_commit_block(txn);
        }
    }
    ovsdb_idl_txn_destroy(txn);

    return;
} /* vrfmgrd_run */

/*
 * Calls ovsdb_idl_wait, which arranges for poll_block() to wake up when
 * ovsdb_idl_run() has something to do or when activity occurs on a
 * transaction on 'idl'.
 */
void
vrfmgrd_wait(void)
{
    ovsdb_idl_wait(idl);
} /* vrfmgrd_wait */
