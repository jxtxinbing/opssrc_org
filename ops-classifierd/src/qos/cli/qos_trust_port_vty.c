/****************************************************************************
 * (c) Copyright 2015-2016 Hewlett Packard Enterprise Development LP
 *
 *    Licensed under the Apache License, Version 2.0 (the "License"); you may
 *    not use this file except in compliance with the License. You may obtain
 *    a copy of the License at
 *
 *         http://www.apache.org/licenses/LICENSE-2.0
 *
 *    Unless required by applicable law or agreed to in writing, software
 *    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 *    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 *    License for the specific language governing permissions and limitations
 *    under the License.
 *
 ***************************************************************************/

#include <config.h>

#include "qos_trust_port_vty.h"

#include <libaudit.h>

#include "memory.h"
#include "openswitch-idl.h"
#include "openvswitch/vlog.h"
#include "ovsdb-idl.h"
#include "qos_utils.h"
#include "qos_utils_vty.h"
#include "smap.h"
#include "vswitch-idl.h"
#include "vtysh/command.h"
#include "vtysh/vtysh.h"
#include "vtysh/vtysh_ovsdb_config.h"
#include "vtysh/vtysh_ovsdb_if.h"
#include "vtysh/vtysh_user.h"

VLOG_DEFINE_THIS_MODULE(vtysh_qos_trust_port_cli);
extern struct ovsdb_idl *idl;

const char *
qos_trust_port_get_value(const struct ovsrec_port *port_row)
{
    if (port_row != NULL) {
        const char *port_value = smap_get(&port_row->qos_config, QOS_TRUST_KEY);
        if (port_value != NULL) {
            return port_value;
        }
    }

    const struct ovsrec_system *system_row = ovsrec_system_first(idl);
    if (system_row != NULL) {
        const char *system_value = smap_get(
                &system_row->qos_config, QOS_TRUST_KEY);
        if (system_value != NULL) {
            return system_value;
        }
    }

    return QOS_TRUST_NONE_STRING;
}

/**
 * Executes the trust_port_command for the given port_name and
 * qos_trust_name.
 */
static int
qos_trust_port_command(const char *port_name,
        const char *qos_trust_name)
{
    if (port_name == NULL) {
        vty_out(vty, "port_name cannot be NULL.%s", VTY_NEWLINE);
        return CMD_OVSDB_FAILURE;
    }

    if (qos_trust_name == NULL) {
        vty_out(vty, "qos trust name cannot be NULL.%s", VTY_NEWLINE);
        return CMD_OVSDB_FAILURE;
    }

    if (is_member_of_lag(port_name)) {
        vty_out(vty, "QoS Trust cannot be configured on a member of a LAG.%s",
                VTY_NEWLINE);
        return CMD_OVSDB_FAILURE;
    }

    struct ovsrec_port *port_row = port_row_for_name(port_name);
    if (port_row == NULL) {
        vty_out(vty, "Port %s does not exist.%s",
                port_name, VTY_NEWLINE);
        return CMD_OVSDB_FAILURE;
    }

    struct ovsdb_idl_txn *txn = cli_do_config_start();
    if (txn == NULL) {
        vty_out(vty, "Unable to start transaction.%s", VTY_NEWLINE);
        VLOG_ERR(OVSDB_TXN_CREATE_ERROR);
        return CMD_OVSDB_FAILURE;
    }

    struct smap smap;
    smap_clone(&smap, &port_row->qos_config);
    smap_replace(&smap, QOS_TRUST_KEY, qos_trust_name);
    ovsrec_port_set_qos_config(port_row, &smap);
    smap_destroy(&smap);

    enum ovsdb_idl_txn_status status = cli_do_config_finish(txn);
    if (status != TXN_SUCCESS && status != TXN_UNCHANGED) {
        vty_out(vty, "Unable to commit transaction.%s", VTY_NEWLINE);
        VLOG_ERR(OVSDB_TXN_COMMIT_ERROR);
        return CMD_OVSDB_FAILURE;
    }

    return CMD_SUCCESS;
}

/**
 * Executes the trust_port_command.
 */
DEFUN(qos_trust_port,
        qos_trust_port_cmd,
        "qos trust (none|cos|dscp)",
        QOS_HELP_STRING
        "Set the QoS Trust Mode configuration for the port\n"
        "Do not trust any priority fields, and \
remark all of them to 0 (Default)\n"
        "Trust 802.1p priority and preserve DSCP or IP-ToS\n"
        "Trust DSCP and remark the 802.1p priority to match\n")
{
    char aubuf[QOS_CLI_AUDIT_BUFFER_SIZE] = "op=CLI: qos trust";

    const char *port_name = (char*) vty->index;
    qos_audit_encode(aubuf, sizeof(aubuf), "port_name", port_name);

    const char *qos_trust_name = argv[0];
    qos_audit_encode(aubuf, sizeof(aubuf), "qos_trust_name", qos_trust_name);

    int result = qos_trust_port_command(port_name, qos_trust_name);

    qos_audit_log(aubuf, result);

    return result;
}

/**
 * Executes the trust_port_no_command for the given port_name.
 */
static int
qos_trust_port_no_command(const char *port_name)
{
    if (port_name == NULL) {
        vty_out(vty, "port_name cannot be NULL.%s", VTY_NEWLINE);
        return CMD_OVSDB_FAILURE;
    }

    if (is_member_of_lag(port_name)) {
        vty_out(vty, "QoS Trust cannot be configured on a member of a LAG.%s",
                VTY_NEWLINE);
        return CMD_OVSDB_FAILURE;
    }

    struct ovsrec_port *port_row = port_row_for_name(port_name);
    if (port_row == NULL) {
        vty_out(vty, "Port %s does not exist.%s", port_name, VTY_NEWLINE);
        return CMD_OVSDB_FAILURE;
    }

    struct ovsdb_idl_txn *txn = cli_do_config_start();
    if (txn == NULL) {
        vty_out(vty, "Unable to start transaction.%s", VTY_NEWLINE);
        VLOG_ERR(OVSDB_TXN_CREATE_ERROR);
        return CMD_OVSDB_FAILURE;
    }

    struct smap smap;
    smap_clone(&smap, &port_row->qos_config);
    smap_remove(&smap, QOS_TRUST_KEY);
    ovsrec_port_set_qos_config(port_row, &smap);
    smap_destroy(&smap);

    enum ovsdb_idl_txn_status status = cli_do_config_finish(txn);
    if (status != TXN_SUCCESS && status != TXN_UNCHANGED) {
        vty_out(vty, "Unable to commit transaction.%s", VTY_NEWLINE);
        VLOG_ERR(OVSDB_TXN_COMMIT_ERROR);
        return CMD_OVSDB_FAILURE;
    }

    return CMD_SUCCESS;
}

/**
 * Executes the trust_port_no_command.
 */
DEFUN(qos_trust_port_no,
        qos_trust_port_no_cmd,
        "no qos trust {none|cos|dscp}",
        NO_STR
        QOS_HELP_STRING
        "Remove the QoS Trust Mode configuration for the port\n"
        "Do not trust any priority fields, and \
remark all of them to 0 (Default)\n"
        "Trust 802.1p priority and preserve DSCP or IP-ToS\n"
        "Trust DSCP and remark the 802.1p priority to match\n")
{
    char aubuf[QOS_CLI_AUDIT_BUFFER_SIZE] = "op=CLI: no qos trust";

    const char *port_name = (char*) vty->index;
    qos_audit_encode(aubuf, sizeof(aubuf), "port_name", port_name);

    int result = qos_trust_port_no_command(port_name);

    qos_audit_log(aubuf, result);

    return result;
}

/**
 * Initializes qos_trust_port_vty.
 */
void
qos_trust_port_vty_init(void)
{
    install_element(INTERFACE_NODE, &qos_trust_port_cmd);
    install_element(INTERFACE_NODE, &qos_trust_port_no_cmd);

    install_element(LINK_AGGREGATION_NODE, &qos_trust_port_cmd);
    install_element(LINK_AGGREGATION_NODE, &qos_trust_port_no_cmd);
}

/**
 * Initializes qos_trust_port_ovsdb.
 */
void
qos_trust_port_ovsdb_init(void)
{
    ovsdb_idl_add_table(idl, &ovsrec_table_port);
    ovsdb_idl_add_column(idl, &ovsrec_port_col_qos_config);
}
