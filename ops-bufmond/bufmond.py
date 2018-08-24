#!/usr/bin/env python
# (c) Copyright [2015-2016] Hewlett Packard Enterprise Development LP
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# A daemon to add buffer monitoring counter to the OVSDB bufmon table and
# Updates the capability information to system OVSDB tables.
# Its responsibilities include:
#
# - Add the buffer monitoring global configuration to the System table".
# - Add the buffer counters list to the "bufmon" table.

'''
NOTES:
Expected bufmond.yaml file format for counters list

cap_mode_current: true
cap_mode_peak: true
cap_snapshot_on_threshold_trigger: true
cap_threshold_trigger_collection: true
counters:
- name: device/data/NONE/NONE
  counter_vendor_specific_info:
    counter_name: data
  hw_unit_id: 0
- name: ingress-port-priority-group/um-share-buffer-count/1/1
  counter_vendor_specific_info:
    counter_name: um-share-buffer-count
    port: '1'
    priority-group: '1'
  hw_unit_id: 0
 '''

import argparse
import os
import sys
import time
from time import sleep

import ovs.dirs
from ovs.db import error
from ovs.db import types
import ovs.daemon
import ovs.db.idl
import ovs.unixctl
import ovs.unixctl.server

# OVS definitions.
idl = None

# Tables definitions.
SYSTEM_TABLE = 'System'
SUBSYTEM_TABLE = 'Subsystem'
BUFMON_TABLE = 'bufmon'

# Columns definitions.
SYSTEM_CUR_CFG = 'cur_cfg'
SYSTEM_BUFMON_CONFIG_COLUMN = 'bufmon_config'
SYSTEM_BUFMON_INFO_COLUMN = 'bufmon_info'

SUBSYSTEM_HW_DESC_DIR_COLUMN = 'hw_desc_dir'

BUFMON_HW_UNIT_ID_COLUMN = 'hw_unit_id'
BUFMON_NAME_COLUMN = 'name'
BUFMON_COUNTER_VENDOR_INFO_COLUMN = 'counter_vendor_specific_info'
BUFMO_ENABLED_COLUMN = 'enabled'
BUFMON_TRIGGER_THRESHHOLD_COLUMN = 'trigger_threshold'
BUFMON_COUNTER_VALUE_COLUMN = 'counter_value'
BUFMON_STATUS_COLUMN = 'status'

# Default DB path.
def_db = 'unix:/var/run/openvswitch/db.sock'

# TODO: Need to pull these from the build env.
ovs_schema = '/usr/share/openvswitch/vswitch.ovsschema'

# YAML definitions.
YAML_FILE_PATH = '/bufmond.yaml'
YAML_COUNTERS_ROOT = 'counters'

vlog = ovs.vlog.Vlog("bufmond")
exiting = False
seqno = 0


def unixctl_exit(conn, unused_argv, unused_aux):
    global exiting
    exiting = True
    conn.reply(None)


#------------------ parse_bufmond_yaml() ----------------
def parse_bufmond_yaml():
    import yaml
    global yaml_data

    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader

    with open(YAML_FILE_PATH) as fh:
        yaml_data = yaml.load(fh, Loader=Loader) or {}

    return yaml_data != {}


#------------------ ovsdb_set_bufmon_config() ----------------
def ovsdb_set_bufmon_config():
    global idl
    data = {}
    ret = False
    # Default values for system table bufmon_config.
    data["enabled"] = "false"
    data["counters_mode"] = "peak"
    data["periodic_collection_enabled"] = "false"
    data["collection_period"] = "5"
    data["threshold_trigger_collection_enabled"] = "true"
    data["threshold_trigger_rate_limit"] = "60"
    data["threshold_trigger_collection_enabled"] = "true"
    data["snapshot_on_threshold_trigger"] = "true"

    for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
        setattr(ovs_rec, SYSTEM_BUFMON_CONFIG_COLUMN, data)
        ret = True
        break

    return ret


#------------------ ovsdb_update_bufmon_info() ----------------
def ovsdb_set_bufmon_info(ovsrec_bufmon_info):
    '''
    Update the counter capability information to System table
    '''
    global idl
    ret = False

    for ovs_rec in idl.tables[SYSTEM_TABLE].rows.itervalues():
        setattr(ovs_rec, SYSTEM_BUFMON_INFO_COLUMN, ovsrec_bufmon_info)
        ret = True
        break

    return ret


#------------------ ovsdb_set_bufmon() ----------------
def ovsdb_set_bufmon(ovsrec_row, counter):
    '''
    Update the counter details to bufmon table
    '''
    for column, value in counter.iteritems():
        # validate column name present in the bufmon table.
        if column not in ovsrec_row._table.columns:
            vlog.warn("bufmon table invalid column '%s' " % column)
            continue
        else:
            setattr(ovsrec_row, column, value)
            vlog.dbg("%s %s \n " % (column, value))


#------------------ update_bufmond_config() ----------------
def update_bufmond_config():
    '''
    Update the YAML content to the OVS-DB
    Update the global configuration to System Table
    Update the ASIC supported buffer counters to bufmon Table
    '''

    global yaml_data
    global idl
    global seqno

    ovsrec_openvswitch = {}
    ovsrec_bufmon = {}
    bufmon_global_config = {}
    ret = False

    # create the transaction.
    seqno = idl.change_seqno
    txn = ovs.db.idl.Transaction(idl)

    # create new row in system table to update the configuration.
    ovsrec_openvswitch = idl.tables[SYSTEM_TABLE].rows.itervalues()

    if ovsrec_openvswitch is None:
        return False

    # Default configurations.
    if ovsdb_set_bufmon_config() is False:
        return False

    # Insert new row for each counter in OVS-DB.
    if yaml_data.get(YAML_COUNTERS_ROOT) is not None:
        for key, value in yaml_data.iteritems():
            if YAML_COUNTERS_ROOT in key:
                counters_list = yaml_data[YAML_COUNTERS_ROOT]
                # Add the list of buffer monitoring counters.
                for counter_data in counters_list:
                    ovsrec_bufmon = txn.insert(idl.tables[BUFMON_TABLE])
                    ret = ovsdb_set_bufmon(ovsrec_bufmon,
                                           counter_data)
            else:
                    bufmon_global_config[key] = str(value)

    # Update the system table bufmon_info column.
    if bufmon_global_config is not None:
        ret = ovsdb_set_bufmon_info(bufmon_global_config)

    # commit the transaction.
    status = txn.commit_block()
    vlog.dbg("Buffer monitoring transaction status %s "
             % (ovs.db.idl.Transaction.status_to_string(status)))

    if ret is True and status != ovs.db.idl.Transaction.SUCCESS:
        ret = False

    return ret


#------------------ db_get_system_status() ----------------
def db_get_system_status(data):
    '''
    Checks the system initialization completed System:cur_cfg
    configuration completed: return True
    else: return False
    '''
    for ovs_rec in data[SYSTEM_TABLE].rows.itervalues():
        if ovs_rec.cur_cfg:
            if ovs_rec.cur_cfg == 0:
                return False
            else:
                return True

    return False


#------------------ get_bufmond_yaml_file_status() ----------------
def get_bufmond_yaml_file_status(data):
    '''
    Checks the yaml is exists
    if yaml file exists: return True
    else: return False
    '''
    global idl
    global YAML_FILE_PATH
    ret = False

    for ovs_rec in data[SUBSYTEM_TABLE].rows.itervalues():
        if ovs_rec.hw_desc_dir:
            if not ovs_rec.hw_desc_dir is None:
                YAML_FILE_PATH = ovs_rec.hw_desc_dir + YAML_FILE_PATH
                return os.path.exists(YAML_FILE_PATH)

    return False


#------------------ system_is_configured() ----------------
def system_is_configured():
    global idl
    global exiting
    global YAML_FILE_PATH

    # Check the OVS-DB/File status to see if initialization has completed.
    if not db_get_system_status(idl.tables):
        # Delay a little before trying again.
        sleep(1)
        return False
    elif not get_bufmond_yaml_file_status(idl.tables):
        exiting = True
        vlog.info('File %s not found. bufmond Exiting' % YAML_FILE_PATH)
        return False

    return True


#------------------ check_counters_list_is_empty() ----------------
def check_counters_list_is_empty():
    '''
    Checks list of counters already configured in the OVS-DB
    If counter rows not exits : return True
    else: return False and Exit
    '''

    global idl
    global exiting

    # counters list already configured avoid over writing.
    for ovs_rec in idl.tables[BUFMON_TABLE].rows.itervalues():
        if ovs_rec is not None:
            # Exiting Daemon.
            exiting = True
            vlog.info('bufmon counters list already configured')
            return False

    return True


#------------------ terminate() ----------------
def terminate():
    global exiting
    # Exiting Daemon.
    exiting = True


#------------------ bufmond_init() ----------------
def bufmond_init(remote):
    '''
    Initializes the OVS-DB connection
    '''

    global idl

    schema_helper = ovs.db.idl.SchemaHelper(location=ovs_schema)
    schema_helper.register_columns(SYSTEM_TABLE,
                                   [SYSTEM_CUR_CFG,
                                    SYSTEM_BUFMON_CONFIG_COLUMN,
                                    SYSTEM_BUFMON_INFO_COLUMN])
    schema_helper.register_columns(SUBSYTEM_TABLE,
                                   [SUBSYSTEM_HW_DESC_DIR_COLUMN, ])
    schema_helper.register_columns(BUFMON_TABLE,
                                   [BUFMON_HW_UNIT_ID_COLUMN,
                                    BUFMON_NAME_COLUMN,
                                    BUFMON_COUNTER_VENDOR_INFO_COLUMN,
                                    BUFMO_ENABLED_COLUMN,
                                    BUFMON_TRIGGER_THRESHHOLD_COLUMN,
                                    BUFMON_COUNTER_VALUE_COLUMN,
                                    BUFMON_STATUS_COLUMN])

    idl = ovs.db.idl.Idl(remote, schema_helper)


#------------------ bufmond_reconfigure() ----------------
def bufmond_reconfigure():

    # System configuration is not completed.
    if system_is_configured() is False:
        return

    # Check the counter list is already populated in OVS-DB.
    if check_counters_list_is_empty() is False:
        return

    # Parse the bufmond counters list YAML file.
    if parse_bufmond_yaml() is False:
        return

    # Update the counters to OVS-DB.
    if update_bufmond_config() is False:
        return

    # Counters list added successfully Exiting the Daemon.
    terminate()


#------------------ bufmond_run() ----------------
def bufmond_run():

    global idl
    global seqno

    idl.run()

    if seqno != idl.change_seqno:
        bufmond_reconfigure()
        seqno = idl.change_seqno


#------------------ bufmond_wait() ----------------
def bufmond_wait():
        pass


#------------------ main() ----------------
def main():

    global exiting
    global idl
    global seqno

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', metavar="DATABASE",
                        help="A socket on which ovsdb-server is listening.",
                        dest='database')

    ovs.vlog.add_args(parser)
    ovs.daemon.add_args(parser)
    args = parser.parse_args()
    ovs.vlog.handle_args(args)
    ovs.daemon.handle_args(args)

    if args.database is None:
        remote = def_db
    else:
        remote = args.database

    bufmond_init(remote)

    ovs.daemon.daemonize()

    ovs.unixctl.command_register("exit", "", 0, 0, unixctl_exit, None)
    error, unixctl_server = ovs.unixctl.server.UnixctlServer.create(None)

    if error:
        ovs.util.ovs_fatal(error, "could not create unix-ctl server", vlog)

    # Sequence number when we last processed the db.
    seqno = idl.change_seqno

    exiting = False
    while not exiting:

        bufmond_run()

        unixctl_server.run()

        bufmond_wait()

        if exiting:
            break

        if seqno == idl.change_seqno:
            poller = ovs.poller.Poller()
            unixctl_server.wait(poller)
            idl.wait(poller)
            poller.block()

    # Daemon Exit.
    unixctl_server.close()
    idl.close()


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        # Let system.exit() calls complete normally.
        raise
    except:
        vlog.exception("traceback")
        sys.exit(ovs.daemon.RESTART_EXIT_CODE)
